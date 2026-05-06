### Sea-Bird / BeanSea VPBT Collaboration

#### Prerequisites

VPBT apps assume data is in /Box-Box/BeamSeaBird/data/355-532 VPBT/*  configuration filesin
/Box-Box/BeamSeaBird/data/355-532 VPBT/data/PMT/*. This can be easily established by installing the Box app on your Mac or PC and syncing up  (just like Dropbox, OpenDrive, or Google Drive).

Your tree below /Box-Box/BeamSeaBird/ should look minimally look like this:
```
├── code
│   ├── __init__.py
│   ├── newiris
│   ├── README.md
│   ├── retrieval1
│   ├── shared
├── data
│   ├── 355_532 VPBT
│   ├── PMT
```
#### Flask apps:

* waveform / pipeline results viewer

newiris/app.py (port 5001)  

```
cd /Box-Box/BeamSeaBird/code/retrieval1
pip install -r requirements.txt
cd ..
python newiris/app.py
# Browse to http://127.0.0.1:5001/
```

* retrieval attempt1

retrieval/app.py (port 5002)  

```
cd /Box-Box/BeamSeaBird/code/retrieval1
pip install -r requirements.txt  
cd ..
python retrieval1/app.py
# Browse to http://127.0.0.1:5002/
```


<img width="1745" height="2194" alt="newiris" src="https://github.com/user-attachments/assets/c48bf061-44ff-441a-b537-237a35f69d3c" />

<img width="2230" height="2194" alt="retrieval1" src="https://github.com/user-attachments/assets/6df22477-28f3-4cb7-8dcb-ed701c45e4e2" />

