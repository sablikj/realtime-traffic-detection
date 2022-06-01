Pro správné fungování aplikace je potřeba build knihovny OpenCV obsahující modul GStreamer a CUDA DNN.
V .env souboru chybí údaje pro připojení k databázi, takže se data ukládají pouze lokálně ve formátu CSV.
Databáze by měla obsahovat dvě tabulky: 
	Vehicles(VehicleID: int,
		 Class: varchar, 
		 IntersectionOrigin: varchar,
                 IntersectionExit:varchar, 
                 Timestamp: Datetime
		)
	PositionPoints(PointID: int,
		       X_value: int,
		       Y_value: int,
	               VehicleID: int
		      )

