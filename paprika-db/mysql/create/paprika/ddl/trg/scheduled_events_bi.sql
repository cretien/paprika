delimiter |

CREATE TRIGGER scheduled_events_bi BEFORE INSERT ON scheduled_events
  FOR EACH ROW BEGIN
    DECLARE hash VARCHAR(255);
    SELECT MD5(CONCAT(RAND(), NOW())) INTO hash;
	SET NEW.created_at=NOW();
    SET NEW.created_by=CURRENT_USER();
    SET NEW.updated_at=NOW();
    SET NEW.updated_by=CURRENT_USER();
    SET NEW.hashcode=hash;
  END;
|

delimiter ;