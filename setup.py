import codecs
from setuptools import setup, find_packages

requirements = [
    'python-networkmanager',
    'click'
]

with codecs.open("README.md", "r", encoding='utf-8') as desc_file:
    long_description = desc_file.read()

if __name__ == '__main__':
    setup(
        name='wifi-backup',
        version='0.0.1',
        description='Backup and Import wifi passwords over dbus.',
        long_description=long_description,
        long_description_content_type="text/markdown",
        url='https://github.com/fliiiix/wifi-backup',
        author='Fliiiix',
        author_email='hi@l33t.name',
        maintainer='Fliiiix',
        maintainer_email='hi@l33t.name',
        include_package_data=True,
        package_data={'': ['README.md']},
        package_dir={"": "src"},
        packages=find_packages(where="src"),
        install_requires=requirements,
        entry_points = {
            'console_scripts': [
                'wifi=wifibackup.wifi:cli'
            ],
        },
        classifiers=[
            'Environment :: Console',
            'License :: OSI Approved :: MIT License',
            'Operating System :: POSIX',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: Implementation',
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: PyPy'
        ]
    )
