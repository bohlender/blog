---
title: "Turning Studio Headphones Into a Headset"
date: 2023-01-21T13:38:05+01:00
tags: ["Tinkering"]
draft: true
math: false
images: []
videos: []
audio: []
---
In a recent virtual meeting a new colleague was surprised to see me using a [Beyerdynamic DT 770 PRO](https://beyerdynamic.com/dt-770-pro.html) _headset_ -- a product Beyerdynamic does not even list.
The DT 770 PRO are well-known studio _headphones_, and so are all the other entries in Beyerdynamic's <q>studio</q> line.
Only their <q>gaming</q> line of products features headsets.
So how could I possibly be using a device that does not seem to exist?

The solution is unspectacular if one is aware of "detachable microphones".
To turn a wired studio headphone into a headset all one needs to do is to make it possible to attach such a microphone.
This post illustrates
- how replacing the integrated headphone cable by an [audio jack](https://en.wikipedia.org/wiki/Phone_connector_(audio)) achieves this,
- the concrete implementation using my DT 770 PRO as a test object.
<!--more-->
## Introduction
I've owned [Beyerdynamic DT 770 PRO](https://beyerdynamic.com/dt-770-pro.html) studio headphones for ages.
However in the past I could not use them to participate in virtual meetings or for voice chat in multiplayer games.
Instead, I resorted to various headsets even though I was always left dissatisfied with their wear comfort and sound.

{{<note>}}
I was aware of "attachable microphones", such as the [Antlion ModMic](https://antlionaudio.com/collections/microphones), but neither did I want to put an adhesive pad of questionable reliability on my headphones nor did I want to have to deal with an additional cable just for the microphone.
{{</note>}}

Using a professional microphone and audio interface for these use cases felt like overkill.
I was rather saying to myself that, once my headphones would break, I would eventually see to find to a model with an audio jack.
This would enable me to plug in some "detachable microphone", like the [Beyerdynamic CUSTOM Headset Gear](https://beyerdynamic.com/custom-headset-gear-2-generation.html) or [V-MODA BoomPro](https://www.v-moda.com/us/en/products/boompro-microphone).
With this "solution" sketched out I didn't really look into the issue anymore.

About a year ago, when it was once again time to replace the ear pads, it occurred to me that -- while I was at it -- I could also simply replace the integrated headphone cable by a 3.5mm [audio jack](https://en.wikipedia.org/wiki/Phone_connector_(audio)).
It was only when I started looking for suitable components that I noticed my tinkering project to actually be a [pretty standard modification](https://duckduckgo.com/?q=studio+headphones+detachable+cable+mod).
It is a trivial mod, but I figured I should spread the word.
Had I been aware of it, I wouldn't have spent all these years with regular headsets.

## The Modification in Theory
To better understand the initial situation, consider the following sketch of the wiring in the unmodified headphones.
The scale of some parts is a bit exaggerated to make relevant details more visible.

{{<figure src="gfx/sketch1.svg" title="Wiring in the unmodified headphones" width="600">}}

The depicted audio plug is a [TRS connector](https://en.wikipedia.org/wiki/TRS_connector).
It exposes three conductors which the integrated cable connects to a small [PCB](https://en.wikipedia.org/wiki/Printed_circuit_board) inside the headphone housing.
This PCB, in turn, is wired to the left and right loudspeaker.
Aside from the obligatory [ground](https://en.wikipedia.org/wiki/Ground_(electricity)) reference point the conductors are designed to transmit the left and right audio channel signals.

{{<note id="test-note">}}
The wire colours in the sketch are picked so that they match the colours present in _my_ headphones.
They might differ in yours so -- if you plan to follow along -- make sure to [test](https://en.wikipedia.org/wiki/Continuity_test) which part of the TRS connector each of the PCB wires connects to.
{{</note>}}

It should be easy to see that the integrated cable can readily be turned into a detachable one by cutting through it and attaching matching connectors to both ends.
It is advisable to cut the wires _inside_ the housing -- in contrast to cutting the cable outside -- as this enables fitting the jack into the housing.

{{<figure src="gfx/sketch2.svg" title="Wiring in the modified headphones" width="600">}}

{{<note>}}
A jack features three contacts and -- unlike in the sketch -- it's not visible which conductor each contact is designed for.
While the middle contact will typically connect to the sleeve, make sure to check the data sheet of the jack you're getting to not end up with swapped audio channels.
{{</note>}}

That's already it.
At this point one can just plug in a detachable microphone into the headphones to turn them into a headset, or stick to the detachable cable when no mic is needed.
To make it obvious why and how this works, let's put the wiring of a detachable microphone in the context of the modified headphone.

{{<figure src="gfx/sketch3.svg" title="Wiring in the modified headphones and detachable microphone" width="600">}}

The detachable microphone looks a lot like the detachable cable from the previous sketch, with the exception that this one has an additional wire for the microphone signal.
A quick look at the wiring confirms that a detachable microphone is essentially just a cable housing two decoupled products: a mono microphone and a stereo phone cable.
They just happen to share the ground wire.
The headphones couldn't care less whether the detachable microphone is plugged in or the detachable cable -- it's the same TRS connector and the same signals in both cases.

The [TRRS connector](https://en.wikipedia.org/wiki/Phone_connector_(audio)#TRRS_standards) on the other end is what goes into the computer.
It's the standard way of supporting both headphones and headsets on the same jack.

{{<note>}}
Unlike mobile devices, desktop computers often don't feature TRRS jacks but distinct TRS jacks for headphones and microphone.
For this case, detachable microphones usually come with a TRRS splitter to separate the signals accordingly.
{{</note>}}

## The Modification in Practice
Replacing the integrated headphone cable by an audio jack resolves a real annoyance for me.
I figured it might do so for others and did therefore document every (mis)step of the process.

Overall the modification requires
- a drill to turn the rectangular hole for the integrated cable into a circular hole for the jack,
- something like a small, flat screwdriver to lever up some parts,
- something to cut the cable and remove insulation from wires -- a knife or scalpel will do,
- matching TRS connectors, i.e. a jack ([PMA-009494](https://www.kenable.co.uk/en/audio-/audio-connectors/audio-adapters/9494-35mm-aux-stereo-socket-input-panel-mount-audio-solder-adapter-2-pack-009494-5055383494941.html)) and a plug ([NYS231BG](https://www.rean-connectors.com/en/product/nys231-1)),
- small pliers to screw the jack into the housing,
- a soldering iron to make the electrical connections permanent.

{{<note>}}
If you can't get ahold of the same jack, you can give the [MJ-0073H](https://www.farnell.com/datasheets/3144941.pdf) a try.
It's the same thing, except that "Contact C" is 6.5mm long instead of 5mm.
You should probably avoid [PJ-392A](https://aliexpress.com/item/1005003621329893.html) though since that one will stick out a bit further from the headphone housing.
{{</note>}}

### Step 1: Opening the Housing
To replace the integrated audio cable, we must cut through it _inside_ the headphone housing.
For this, we first need to open the housing.
This amounts to peeling off the ear pad and removing the clamping ring.

{{<note>}}
There's even [official documentation](https://support.beyerdynamic.com/hc/en-us/articles/360017577334-Caring-and-replacing-the-ear-pads) on how one is supposed to open the housing, e.g. to replace the ear pads.
{{</note>}}

{{<gallery>}}
    {{<figure
        caption="The unmodified headphones"
        src="gfx/DSC05510.jpg"
        src-next="gfx/DSC05513.jpg">}}
    {{<figure
        caption="A bit of pulling suffices to peel the ear pad off the housing"
        src="gfx/DSC05513.jpg"
        src-prev="gfx/DSC05510.jpg"
        src-next="gfx/DSC05514.jpg">}}
    {{<figure
        caption="This ear pad was already yellowing and really needed to be replaced"
        src="gfx/DSC05514.jpg"
        src-prev="gfx/DSC05513.jpg"
        src-next="gfx/DSC05519.jpg">}}
    {{<figure
        caption="The clamping ring is held by a few clips and can be levered up with a flat screwdriver. I recommend inserting the screwdriver as shown here, i.e. on the outside of the ring. Poking around with it on the inside of the ring risks accidentially piercing into the white paper sheet that sits right under the black foam pad."
        src="gfx/DSC05519.jpg"
        src-prev="gfx/DSC05514.jpg"
        src-next="gfx/DSC05520.jpg">}}
    {{<figure
        caption="The speaker is attached to the back of this paper sheet"
        src="gfx/DSC05520.jpg"
        src-prev="gfx/DSC05519.jpg"
        src-next="gfx/DSC05521.jpg">}}
    {{<figure
        caption="Here we can see the blue, red and copper wires from the above diagrams"
        src="gfx/DSC05521.jpg"
        src-prev="gfx/DSC05520.jpg">}} 
{{</gallery>}}

### Step 2: Cutting the Integrated Cable
Instead of adding an additional hole to the housing, the plan is to repurpose the one occupied by the integrated cable.
That is, the cable must must be removed to make place for a jack.
It is advantageous to cut through the wires as far from the PCB as possible since we'll later have to solder them to the jack.

{{<note>}}
As suggested [earlier](#test-note), you better [test](https://en.wikipedia.org/wiki/Continuity_test) which part of the TRS connector each of the wires connects to.
In my case, the T, R and S conductors connect to the blue, red & copper wire, respectively.
{{</note>}}

{{<gallery>}}
    {{<figure
        caption="This clip must be levered up to unclamp the cable"
        src="gfx/DSC05533.jpg"
        src-next="gfx/DSC05538.jpg">}} 
    {{<figure
        caption="With the clip removed the cable can be moved freely"
        src="gfx/DSC05538.jpg"
        src-prev="gfx/DSC05533.jpg"
        src-next="gfx/DSC05541.jpg">}} 
    {{<figure
        caption="Pulling the cable out makes the wires easily accessible"
        src="gfx/DSC05541.jpg"
        src-prev="gfx/DSC05538.jpg"
        src-next="gfx/DSC05545.jpg">}} 
    {{<figure
        caption="The optimal cut maximises the wire lengh"
        src="gfx/DSC05545.jpg"
        src-prev="gfx/DSC05541.jpg"
        src-next="gfx/DSC05548.jpg">}} 
    {{<figure
        src="gfx/DSC05548.jpg"
        src-prev="gfx/DSC05545.jpg">}} 
{{</gallery>}}

### Step 3: Attaching a Plug to the Cable
By attaching another plug to the cut cable one can easily turn it into a detachable cable, rather than throwing it away.

{{<gallery>}}
    {{<figure
        caption="This segment can be cut"
        src="gfx/DSC05551.jpg"
        src-next="gfx/DSC05558.jpg">}} 
    {{<figure
        caption="To get to the wires, a bit of the cable jacket needs to be removed"
        src="gfx/DSC05558.jpg"
        src-prev="gfx/DSC05551.jpg"
        src-next="gfx/DSC05563.jpg">}} 
    {{<figure
        caption="To prepare the wires for soldering, the insulators must be removed."
        src="gfx/DSC05563.jpg"
        src-prev="gfx/DSC05558.jpg"
        src-next="gfx/DSC05564.jpg">}} 
    {{<figure
        src="gfx/DSC05564.jpg"
        src-prev="gfx/DSC05563.jpg"
        src-next="gfx/DSC05572.jpg">}} 
    {{<figure
        caption="Before installing the TRS connector, the boot and tube must be slid onto the cable"
        src="gfx/DSC05572.jpg"
        src-prev="gfx/DSC05564.jpg"
        src-next="gfx/DSC05575.jpg">}} 
    {{<figure
        caption="The wires are positioned in such a way that the plugs' same-named contacts end up connected, i.e. T to T, R to R, and S to S. The clamp secures the cable."
        src="gfx/DSC05575.jpg"
        src-prev="gfx/DSC05572.jpg"
        src-next="gfx/DSC05578.jpg">}} 
    {{<figure
        caption="Soldering the wires creates a permanent electrical connection"
        src="gfx/DSC05578.jpg"
        src-prev="gfx/DSC05575.jpg"
        src-next="gfx/DSC05583.jpg">}} 
    {{<figure
        src="gfx/DSC05583.jpg"
        src-prev="gfx/DSC05578.jpg"
        src-next="gfx/DSC05584.jpg">}} 
    {{<figure
        caption="The finished detachable cable"
        src="gfx/DSC05584.jpg"
        src-prev="gfx/DSC05583.jpg">}} 
{{</gallery>}}

### Step 4: Attaching a Jack to the Headphone
The jack doesn't quite fit into the rectangular hole of the integrated cable.
The hole must be enlarged a little bit to make it possible to screw the jack into the housing.
Then the wires can be soldered to the jack.

{{<note>}}
The data sheet of the jack should state which of its contacts correspond to T, R and S.
Alternatively, to play it safe, you can simply plug your new detachable cable into the jack and [test](https://en.wikipedia.org/wiki/Continuity_test) which contacts of the jack connect to the T, R and S conductors of the plug.
{{</note>}}

{{<gallery>}}
    {{<figure
        caption="To prepare the wires for soldering, the insulators must be peeled off"
        src="gfx/DSC05591.jpg"
        src-next="gfx/DSC05595.jpg">}} 
    {{<figure
        caption="The jack does not fit in yet"
        src="gfx/DSC05595.jpg"
        src-prev="gfx/DSC05591.jpg"
        src-next="gfx/DSC05599.jpg">}} 
    {{<figure
        caption="A 6mm rotary burr produces an opening of just the right size"
        src="gfx/DSC05599.jpg"
        src-prev="gfx/DSC05595.jpg"
        src-next="gfx/DSC05609.jpg">}} 
    {{<figure
        caption="At first the jack can be screwn in with the fingers ..."
        src="gfx/DSC05609.jpg"
        src-prev="gfx/DSC05599.jpg"
        src-next="gfx/DSC05611.jpg">}} 
    {{<figure
        caption="... but to get it really tight pliers are needed."
        src="gfx/DSC05611.jpg"
        src-prev="gfx/DSC05609.jpg"
        src-next="gfx/DSC05617.jpg">}} 
    {{<figure
        caption="In particular, pliers are needed to fasten the nut."
        src="gfx/DSC05617.jpg"
        src-prev="gfx/DSC05611.jpg"
        src-next="gfx/DSC05623.jpg">}} 
    {{<figure
        caption="Originally, these wires were connected to the three conductors (T, R, S) of the plug. They are now soldered to the corresponding T, R and S contacts of the jack."
        src="gfx/DSC05623.jpg"
        src-prev="gfx/DSC05617.jpg"
        src-next="gfx/DSC05639.jpg">}} 
    {{<figure
        caption="Due to the (avoidable) drilling mistake mentioned a few pictures back, the jack occupied more vertical space than the integrated cable did previously. I had to grind off the upper part of the nut to recover the necessary room for seating the other components."
        src="gfx/DSC05639.jpg"
        src-prev="gfx/DSC05623.jpg">}}
{{</gallery>}}

### Step 5: Closing the Housing
Before putting the headphones back together again, plug them into some audio source to make sure they still work after the modification.
If they don't, there's probably a loose connection somewhere.

{{<gallery>}}
    {{<figure
        caption="Unless the jack has been mounted too high, the paper sheet should fit just as it did originally"
        src="gfx/DSC05628.jpg"
        src-next="gfx/DSC05642.jpg">}} 
    {{<figure
        caption="The clamping ring on top of the foam pad should click into place"
        src="gfx/DSC05642.jpg"
        src-prev="gfx/DSC05628.jpg"
        src-next="gfx/DSC05646.jpg">}} 
    {{<figure
        caption="The modified headphones can now be used with detachable cables"
        src="gfx/DSC05646.jpg"
        src-prev="gfx/DSC05642.jpg"
        src-next="gfx/DSC05648.jpg">}} 
{{</gallery>}}

{{<figure
    title="Inserting a detachable microphone turns the headphones into a headset"
    src="gfx/DSC05648.jpg"
    src-prev="gfx/DSC05646.jpg">}}

I've been using the modified headphones for about a year without any issues, and I expect to do so for many years to come.