# Python User Language Support
Python User Language Support for [Cloudstate](https://github.com/cloudstateio/cloudstate).

## Installation via source

```
> git clone https://github.com/cloudstateio/python-support.git
Cloning into 'python-support'...

> cd python-support
> python3 -m venv ./venv 
> source ./venv/bin/activate
> python --version     
Python 3.7.3
> pip --version 
> pip install wheel
> pip install .
```

### generate installer
```
python setup.py bdist_wheel
```

### local install
```
python -m pip install dist/cloudstate-<the version>-py3-none-any.whl
```

### build and run tck, including provisional tests for stateless functions. 
```
./extended_tck.sh
```