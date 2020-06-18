#!/usr/bin/env python3

import json
import sys
import os


# Convert NER generated JSON file to IIIF manifest JSON file.
# Usage: ner_to_iiif.py input_ner input_iiif context_json
def main():
    # parse command line arguments
    input_ner = sys.argv[1]     # input file generated by NER in standard AMP json format to convert from
    input_iiif = sys.argv[2]    # input file to feed to NER editor in IIIF json format to convert to
    context_json = sys.argv[3]  # context info as json string needed for creating HMGM tasks    
#     context_json = '{ "submittedBy": "yingfeng", "unitId": "1", "unitName": "Test Unit", "collectionId": "2", "collectionName": "Test Collection", "taskManager": "Jira", "itemId": "3", "itemName": "Test Item", "primaryfileId": "4", "primaryfileName": "Test primaryfile", "primaryfileUrl": "http://techslides.com/demos/sample-videos/small.mp4", "primaryfileMediaInfo": "/tmp/hmgm/mediaInfo.json", "workflowId": "123456789", "workflowName": "Test Workflow" }'
    print ("input_ner: " + input_ner)
    print ("input_iiif: " + input_iiif)
    print ("context_json: " + context_json)

    # parse input NER and context JSON
    context = json.loads(context_json)
    with open(input_ner, 'r') as ner_file:
        ner_data = json.load(ner_file)

    # generate IIIF JSON from inputs 
    iiif_data = generate_iiif_other_fields(context, ner_data)
    iiif_data["annotations"] = generate_iiif_annotations(ner_data)

    # write IIIF JSON to file
    with open(input_iiif, "w") as iiif_file: 
        json.dump(iiif_data, iiif_file) 


# Populate IIIF fields other than annotations, using the provide context and ner_data.
def generate_iiif_other_fields(context, ner_data):
    primaryfile_name = context["primaryfileName"]
    primaryfile_url = context["primaryfileUrl"]
    media_info_path = context["primaryfileMediaInfo"]
    duration = get_media_duration(media_info_path)

    iiif_data = {
        "@context": [
            "http://digirati.com/ns/timeliner",
            "http://www.w3.org/ns/anno.jsonld",
            "http://iiif.io/api/presentation/3/context.json"
        ],
        "id": ner_data["media"]["filename"],    # use NER media filename as Timeliner ID
        "type": "Manifest",
        "label": { "en": [ "Primaryfile " + primaryfile_name ] },
        "summary": { "en": [ "Named Entity Recognition for " + primaryfile_name ] },
        "items": [
            {
            "id": "canvas-1",
            "type": "Canvas",
            "duration": duration,
            "items": [
                {
                "id": "annotation-1",
                "type": "AnnotationPage",
                "items": [
                    {
                    "id": "annotation-1/1",
                    "type": "Annotation",
                    "motivation": "painting",
                    "body": {
                        "id": primaryfile_url,    # media file played by Timeliner, start from beginning
                        "type": "Audio",
                        "duration": duration
                    },
                    "target": "canvas-1"
                    }
                ]
                }
                ]
            }
            ],
        "structures": [
            {
            "id": "range-1",
            "type": "Range",
            "label": { "en": [ "Unique Bubble" ] },
            "tl:backgroundColour": "#ACD4E2",
            "items": [
                {
                "type": "Canvas",
                "id": f"canvas-1#t=0,{duration}"
                }
            ]
            }
        ],
        "tl:settings": {    # CSS features for Timeliner display
            "tl:bubblesStyle": "rounded",
            "tl:blackAndWhite": False,
            "tl:showTimes": False,
            "tl:autoScaleHeightOnResize": False,
            "tl:startPlayingWhenBubbleIsClicked": False,
            "tl:stopPlayingAtTheEndOfSection": False,
            "tl:startPlayingAtEndOfSection": False,
            "tl:zoomToSectionIncrementally": False,
            "tl:showMarkers": True,
            "tl:bubbleHeight": 80,
            "tl:backgroundColour": "#fff",
            "tl:colourPalette": "default"
        }        
    }

    return iiif_data


# Generate IIIF annotations for the given ner_data.
def generate_iiif_annotations(ner_data):
    annotations_items = []

    # create a IIIF annotation for each entity in ner_data 
    for i, entity in enumerate(ner_data["entities"]):
        annotation = {
          "id": f"marker-{i+1}",
          "type": "Annotation",
          "label": { "en": [ entity["text"]  ]  },
          "body": {
            "type": "TextualBody",
            "value": entity["type"],
            "format": "text/plain",
            "language": "en"
          },
          "target": {
            "type": "SpecificResource",
            "source": "canvas-1",
            "selector": {
              "type": "PointSelector",
              "t":  entity["start"]
            }
          }
        }
        annotations_items.append(annotation)

    annotations = [ {
      "type": "AnnotationPage",
      "items": annotations_items
    } ]
    return annotations


# Get media duration from the media info file with the given mediaInfoPath.
def get_media_duration(media_info_path):
    try:
        with open(media_info_path, 'r') as media_info_file:
            media_info = json.load(media_info_file)
            duration = media_info['streams']['audio'][0]['duration']
    except Exception as e:
        print(f"Exception reading media info from {media_info_path}", e)
        duration = 0
    return duration


if __name__ == "__main__":
    main()    
