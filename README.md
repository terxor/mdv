# mdv - Mardown Viewer for local directories

## Features

- Clean styles, convenient to customize
- Directory tree sidebar for quick switching
- Table of contents automatically generates, heading tracking/highlighting
- Searching: both files names and content

## Usage

For convenience, make a symlink

```sh
ln -s ./mdv ~/.local/bin/mdv
```

Start the server.
On first time, it will create a virtual environment and setup all dependencies
in the repo directory.

```sh
mdv -d ~/workspace/scratch -p 5000
```

Suppose directory listing of `~/workspace/scratch` is

```
/home/terxor/workspace/scratch
└── notes
    └── topics
        └── abc.md
```

You can then view the file `abc.md` in three ways:

- `http://localhost:5000/v/notes/topics/abc.md`: Default viewer
- `http://localhost:5000/m/notes/topics/abc.md`: Minimal viewer
- `http://localhost:5000/t/notes/topics/abc.md`: Plaintext form

## Development

To regenerate syntax css:

```sh
pygmentize -S xcode -f html > static/pygments.css
```

Sass standalone binary:

```
curl -fsSL -o sass.tar.gz https://github.com/sass/dart-sass/releases/download/1.91.0/dart-sass-1.91.0-linux-x64.tar.gz
```

### TODOs

- Fix search of terms with special symbols like 'vector<int>'
- Reload button (?)
- Bug: splitlines on None in fuzzysearch (L=43)

--------------------------------------------------------------------------------
