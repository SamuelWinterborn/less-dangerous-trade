# Less-Dangerous-Trade
Very simple trade route finding scripts for Elite Dangerous, inspired by [Trade-Dangerous](https://github.com/eyeonus/Trade-Dangerous). This project is made possible by obtaining data with api calls to EDSM, so please consider supporting them by [patreon](https://www.patreon.com/EDSM) or consider using log software to help them with the game data!

The use case of this tool is quite specific, so be sure to read the use-case description to decide if it fits what u need.

---

## Use Case
This tool is aimed for arriving at destination as quick as possible with trading in betweens, so it's a balance of speed and profit and not profit alone.

I personally like to take a transport mission that goes very far away, so that I can go do watch youtube or do dishes or whatever in-between jumps, and do trading at refueling docks. That's the main reason I created this tool.

---

## Requirements
- Elite Dangerous of course
- Python (I was using 3.9, but any python3 should be fine)
- requests (install with `pip install requests`)

---

## How to Use
First go to your downloaded path `cd <where-this-folder-is>`, and then just use `python main.py`. Alternatively, there's also `main.ipynb` for Jupyter use (I personally prefer this more).

To edit the parameters, you would have to edit the main script (`main.py` or `main.ipynb`) for now. It's actually just a single line: \
`routePlanner = TripPlanner("Ubassi/Bloomfield Platform","Gilya/Kendrick Enterprise",18, minHop=2, deviation=0.7, cargoSpace=104)`\

Explaination:
```
TripPlanner(
    "Ubassi/Bloomfield Platform"   1st parameter, the starting location
    "Gilya/Kendrick Enterprise"    2nd parameter, the final destination
    18                             3rd parameter, your jump range
                                   (remember to factor in cargo weight!)

    minHop=2                       Helps split the route apart. The script
                                   doesn't factor in fuel, so this is to help
                                   break the route for refueling, or just to specify 
                                   For example: I need refuel every 4 jumps,
                                   and it takes 12 jumps to reach destination, 
                                   so I'll set minHop=3.

    deviation=0.7                  Define how far the algorithm can search,
                                   this can greatly impact performance, because
                                   it'll take longer to search for more systems.
                                   I recommend keeping below 1.5, 0 is possible too.

    cargoSpace=104                 How many cargo space do you have.
)

*Note that locations are written as <systemName>/<stationName>, however it is possible to just write <systemName> and let the calculation deal with the station.
```

The result will look something like this:

![result](/git_page/result.png "result looks like this")

Since calculation takes time, the script will also print out log whenever it got a route section ready:
![log](/git_page/log.png "log")\
So user can start the journey even tho the full route has not been calculated yet.

---

## Limitation
Because the script heavily depends on API calls, it could fail if EDSM's server is down. It happens sometimes, however it's usually fine after waiting for a minute and running it again.

It's also not exactly the fastest program too, could take several minutes to finish calculations. And unfortunately there isn't much I can do about that...

At the moment planetary base are set to ignored, but it can be turn on.

---

## To-Do
[ ] Implement command line parsing to avoid main script editing.\
[ ] Implement more API options.

Feel free to suggest/request any features you would like to add!