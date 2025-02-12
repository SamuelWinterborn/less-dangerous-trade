from scripts.classes import TripPlanner

tripPlanner = TripPlanner()
tripPlanner.plan("Ubassi/Bloomfield Platform","Gilya/Kendrick Enterprise",18, minHop=2, deviation=0.7, cargoSpace=104)