# Demo template {#demo-template status=beta}

This is the template for the description of a demo.

First, we describe what is needed, including:

* Robot hardware
* Number of Duckiebots
* Robot setup steps
* Duckietown hardware

<div class='requirements' markdown="1">

Requires: A Duckiebot able to take logs from the camera

Requires: A calibrated camera

Requires: A duckietown complying with the usual standards

Requires: A laptop with Python3

</div>

## Video of expected results {#demo-template-expected}

First, we show a video of the expected behavior (if the demo is succesful).

## Duckietown setup notes {#demo-template-duckietown-setup}

A duckietown complying with the usual standards is required. In particular, the segmentation algorithm is designed to work under the following conditions:

* Uninterrupted white lines complying with standards
* Yellow (middle) lines complying with standards
* Only ducks or duckiebots are allowed to be on the road, cones or other objects should be removed as they won't be detected as obstacles
* Humans, other animals or objects are only allowed outside of the driving lanes
* No particular lighting conditions are required


## Duckiebot setup notes {#demo-template-duckiebot-setup}

No special requirements for duckiebots are needed, except the ability of recording logs from the camera.
Maybe, something regarding the movidus stick if we plan to use the software on the bot

## Pre-flight checklist {#demo-template-pre-flight}

The pre-flight checklist describes the steps that are sufficient to
ensure that the demo will be correct:

Check: operation 1 done

Check: operation 2 done

## Demo instructions {#demo-template-run}

Here, give step by step instructions to reproduce the demo.

Step 1: XXX

Step 2: XXX


## Troubleshooting {#demo-template-troubleshooting}

Add here any troubleshooting / tips and tricks required.

## Demo failure demonstration {#demo-template-failure}

Finally, put here a video of how the demo can fail, when the assumptions are not respected.
