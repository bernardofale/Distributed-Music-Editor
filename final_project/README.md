[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-24ddc0f5d75046c5622901739e7c5dd533143b0c8e959d652212380cedb1ea36.svg)](https://classroom.github.com/a/q9wGcN9U)
# CD 2023 Project

This application stands out not only for removing the vocals from songs but also for removing individual instruments, allowing a musician to replace the original musician's performance with their own. This new service will be available online through a web portal where the musician can upload a music file, analyze the instruments that make up the music, select various instruments, and finally receive a new file in which the music only contains those instruments.
The goal of this project is for students to develop a system that divides the processing task into multiple parallelizable subtasks in order to increase the system's performance.

## Dependencies

For Ubuntu (and other debian based linux), run the following commands:

```bash
sudo apt install ffmpeg
```

## Setup

Run the following commands to setup the environement:
```bash
python3 -m venv venv
source venv/bin/activate

pip install pip --upgrade
pip install -r requirements.txt


```

It is important to install the requirements following the previous instructions.
By default, PyTorch will install the CUDA version of the library (over 4G simple from the virtual environment).
As such, the current instructions force the installation of the CPU version of PyTorch and then installs Demucs.

## Usage

To run test the sample code simple run:
```bash
./run_firstTime.sh
cd app/
uvicorn app:app --reload
```
This will start the fastAPI web server and deploy one mongoDB container, one rabbitMQ container, and 4 workers;
If the /reset endpoint is invoked you should run
```bash
./run_otherTimes.sh
```
## API documentation

The API docs are accessible at http://localhost:8000/docs

## Authors

* **Bernardo Falé** - [mariolpantunes](https://github.com/bernardofale)
* **André Silva Gomes** - [dgomes](https://github.com/andrecastrosilva)

## Adapted from

* **Mário Antunes** - [mariolpantunes](https://github.com/mariolpantunes)
* **Diogo Gomes** - [dgomes](https://github.com/dgomes)
* **Nuno Lau** - [nunolau](https://github.com/nunolau)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
