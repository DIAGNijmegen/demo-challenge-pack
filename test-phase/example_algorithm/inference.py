"""
Example algorithm for Grand Challenge.

Edit this file to implement your algorithm. It contains:

  init_model() — Called once at server startup. Load your model here.
  run(model)   — Called each time the /invoke endpoint is hit. This should read input
                 from /input, run inference, and write output to /output.

Your algorithm's interfaces:

  interf0:
    Inputs:

      - /input/images/color-fundus

      - /input/age-in-months.json

    Outputs:

      - /output/images/binary-vessel-segmentation



Which interface is active for a given invocation is determined by the
inputs.json file at /input/inputs.json — a system-generated file that
describes the input sockets provided for this case.

To test locally:  ./do_test_run.sh
To save for upload to GC:   ./do_save.sh

Any implementation will do as long as it produces the output as prescribed by the interface.

For more details see:
  https://grand-challenge.org/documentation/algorithms/
  https://grand-challenge.org/documentation/runtime-environment/
"""

import glob
import json
from pathlib import Path

import numpy
import SimpleITK
import torch

INPUT_PATH = Path("/input")
OUTPUT_PATH = Path("/output")
RESOURCE_PATH = Path("resources")


def _show_torch_cuda_info():
    print("=+=" * 10)
    print("Collecting Torch CUDA information")
    print(f"Torch CUDA is available: {(available := torch.cuda.is_available())}")
    if available:
        print(f"\tnumber of devices: {torch.cuda.device_count()}")
        print(f"\tcurrent device: { (current_device := torch.cuda.current_device())}")
        print(f"\tproperties: {torch.cuda.get_device_properties(current_device)}")
    print("=+=" * 10)


def init_model():
    """Load and return your model.

    This is called once by app.py during server startup (before /health returns 200).
    The model is then reused across all /invoke calls — so load it here,
    not inside the run() function.
    """
    _show_torch_cuda_info()

    # Example how to set torch to use the GPU (if available)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    model = torch.nn.Linear(10, 1).to(device)

    # Your model will be extracted to `model_dir` at runtime on Grand Challenge.
    # When testing locally, the local `./model` directory is mounted here.
    # When you're ready for testing on Grand Challenge, upload your model as a tarball
    # via Your algorithm > Models on Grand Challenge.
    # For now, just verify that we can read from the model directory
    model_dir = Path("/opt/ml/model")
    with open(
        model_dir / "a_tarball_subdirectory" / "some_tarball_resource.txt", "r"
    ) as f:
        print(f.read())

    return model


def run(model):
    """This is called each time the /invoke endpoint is called.
    This should read input from /input, run inference, and write output to /output.
    """
    # The key is a tuple of the slugs of the input sockets
    interface_key = get_interface_key()

    # Lookup the handler for this particular set of sockets (i.e. the interface)
    handler = {
        ("age-in-months", "color-fundus-image"): interf0_handler,
    }[interface_key]

    # Call the handler
    return handler(model)


def interf0_handler(model):
    # Read the input

    input_color_fundus_image = load_image_file_as_array(
        location=INPUT_PATH / "images/color-fundus",
    )

    input_age_in_months = load_json_file(
        location=INPUT_PATH / "age-in-months.json",
    )

    # Process the inputs: any way you'd like, here we show-case torch
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_input = torch.randn(1, 10).to(device)
    model_output = model(model_input)

    # For now, let us make bogus predictions

    output_binary_vessel_segmentation = numpy.eye(4, 2)

    # Save your output

    write_array_as_image_file(
        location=OUTPUT_PATH / "images/binary-vessel-segmentation",
        array=output_binary_vessel_segmentation,
    )

    return 0


def get_interface_key():
    # The inputs.json is a system generated file that contains information about
    # the inputs that interface with the algorithm
    inputs = load_json_file(
        location=INPUT_PATH / "inputs.json",
    )
    socket_slugs = [sv["socket"]["slug"] for sv in inputs]
    return tuple(sorted(socket_slugs))


def load_json_file(*, location):
    # Reads a json file
    with open(location) as f:
        return json.loads(f.read())


def load_image_file_as_array(*, location):
    # Use SimpleITK to read a file
    input_files = (
        glob.glob(str(location / "*.tif"))
        + glob.glob(str(location / "*.tiff"))
        + glob.glob(str(location / "*.mha"))
    )
    result = SimpleITK.ReadImage(input_files[0])

    # Convert it to a Numpy array
    return SimpleITK.GetArrayFromImage(result)


def write_array_as_image_file(*, location, array):
    location.mkdir(parents=True, exist_ok=True)

    # You may need to change the suffix to .tif to match the expected output
    suffix = ".mha"

    image = SimpleITK.GetImageFromArray(array)
    SimpleITK.WriteImage(
        image,
        location / f"output{suffix}",
        useCompression=True,
    )


if __name__ == "__main__":
    raise SystemExit(run(model=init_model()))
