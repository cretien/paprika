import time
from paprika.executors.ManagedWorker import ManagedWorker
from paprika.repositories.MessageRepository import MessageRepository
from paprika.system.ClassLoader import ClassLoader
from paprika.system.logger.Logger import Logger
from paprika.system.Traceback import Traceback
from paprika.connectors.ConnectorFactory import ConnectorFactory
from paprika.connectors.DatasourceBuilder import DatasourceBuilder
from paprika.repositories.JobRepository import JobRepository


class MessageWorker(ManagedWorker):
    def __init__(self, id, settings, claim, abort, stop):
        ManagedWorker.__init__(self, id, settings, claim, abort, stop)

    def run(self, queue):
        abort = self.get_abort()
        claim = self.get_claim()
        stop = self.get_stop()
        settings = self.get_settings()

        paprika_ds = DatasourceBuilder.build('paprika-ds.json')
        connector = ConnectorFactory.create_connector(paprika_ds)

        logger = Logger(connector, self)

        job_repository = JobRepository(connector)
        job = job_repository.job()
        job_name = job['job_name']

        message = None
        while self.is_running():
            try:
                message = None

                # retrieve the next message
                message_repository = MessageRepository(connector)
                message = message_repository.dequeue(claim, queue)

                if message:
                    consumer = ClassLoader.find(message['consumer'])
                    consumer.action(connector, message)

                    message_repository.state(queue, message, 'PROCESSED')

                # check if we need to abort, can be called from the main thread or other thread
                aborted = abort.is_aborted()
                self.running(not aborted)

                # check if we need to stop, will be set by the agent's WatchWorker thread
                if not aborted:
                    stopped = stop.is_stopped()
                    self.running(not stopped)

                # no message to process
                if not message:
                    connector.close()
                    time.sleep(settings['worker_idle_delay'])

                logger.trace(job_name, 'worker #' + str(self.get_id()) + " executed.")
            except:
                aborted = abort.is_aborted()
                self.running(not aborted)

                if not aborted:
                    stopped = stop.is_stopped()
                    self.running(not stopped)

                result = Traceback.build()
                if message:
                    try:
                        message_repository = MessageRepository(connector)
                        result['id'] = message['id']
                        message_repository.state(queue, result, 'FAILED')
                    except:
                        logger.fatal(job_name, 'Failed to persist message failure')

                logger.fatal(job_name, result['message'], result['backtrace'])
                connector.close()
                time.sleep(settings['worker_exception_delay'])

