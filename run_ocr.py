import os
import io
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/Users/2020shatgiskessell/Downloads/TextAnalysis-9c60ccd419c1.json"

def detect_document(path):
    """Detects document features in an image."""
    from google.cloud import vision
    bounding_boxes = []
    letters = []
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.document_text_detection(image=image)

    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            #print('\nBlock confidence: {}\n'.format(block.confidence))

            for paragraph in block.paragraphs:
                # print('Paragraph confidence: {}'.format(
                #     paragraph.confidence))

                for word in paragraph.words:
                    word_text = ''.join([
                        symbol.text for symbol in word.symbols
                    ])
                    # print('Word text: {} (confidence: {})'.format(
                    #     word_text, word.confidence))

                    for symbol in word.symbols:
                        bounding_boxes.append(symbol.bounding_box)
                        letters.append(symbol.text)
                        # print('\tSymbol: {} (confidence: {})'.format(
                        #     symbol.text, symbol.confidence))
    return bounding_boxes, letters
