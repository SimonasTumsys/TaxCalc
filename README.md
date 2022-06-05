# taxcalc
A simple tax calculator for food delivery couriers in Lithuania

Written with Python, using Kivy and KivyMD libraries.

Able to scan Wolt and Bolt Food PDFs to extract earning and date data. The scanned data is then put into SQLite3 database,
to be queried when statistics are needed.

Stat window:
Made my own Date Picker as I found the default KivyMD date picker too buggy (sometimes the colors change, sometimes the whole app crashes
with no apparent reason, so decided to make my own.

The app is not perfect as I'd have to sacrifice some ease of use for better memory management.

To be improved:
- Memory management in Stat window: no need to initialize a new Widget object every time a button is pressed,
however I'm currently unable to update widgets on some corner cases.
- Cannot deploy to Android yet as Buildozer doesn't support newest KivyMD version. Will have to workaround with older versions,
but need to sort out the colors of the app, which are bugged in the older versions. Bummer.

Screenshots:

![Main Window](/screnshots/calc_window.PNG?raw=true "Main Window")

