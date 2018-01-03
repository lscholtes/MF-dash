# MF-dash

Scripts for BRAC MF dashboard.

- dash_main.py is used to start the dash server and brings together all the callback and layout scripts.
- layout.py defines the layout of the dashboard and initialises the global dashboard variable 'app'.
- All other python scripts define callbacks for various dashboard components.

Data is stored locally and is not included in git repo for obvious security and privacy reasons.

#########
TODO:
- Add some sort of div/reg/area/branch ranking indicator for performance comparison of each variable
- Hide average selection when comparing DRABs
- Exclude present value column from at-a-glance
#########