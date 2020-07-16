# -*- coding: utf-8 -*-


import random
import logging
import json
import prompts


#import http requests library
import requests


from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response

sb = SkillBuilder()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# Built-in Intent Handlers

class GetWindDirectionHandler(AbstractRequestHandler):
    """Handler for wind direction intent"""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_request_type("LaunchRequest")(handler_input) or
                is_intent_name("GetWindDirectionIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In GetWindDirectionHandler")

        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]



        windDirection = WindHelper.getWindDirection()
        windSpeed = str(WindHelper.getWindSpeed())
        logger.info("Wind direction is: "+windDirection)
        speech = data[prompts.WINDDIRECTION_MESSAGE] + windDirection + data[prompts.WINDSPEED_MESSAGE] + windSpeed + " knots"
        #speech = windSpeed
        handler_input.response_builder.speak(speech).set_card(
            SimpleCard("The " + data[prompts.SKILL_NAME] + " is " + windDirection, data[prompts.WINDSPEED_MESSAGE] + windSpeed))

        return handler_input.response_builder.response



class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In HelpIntentHandler")

        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]

        speech = data[prompts.HELP_MESSAGE]
        reprompt = data[prompts.HELP_REPROMPT]
        handler_input.response_builder.speak(speech).ask(
            reprompt).set_card(SimpleCard(
                data[prompts.SKILL_NAME], speech))
        return handler_input.response_builder.response


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In CancelOrStopIntentHandler")

        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]

        speech = data[prompts.STOP_MESSAGE]
        handler_input.response_builder.speak(speech)
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for Fallback Intent.

    AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")

        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]

        speech = data[prompts.FALLBACK_MESSAGE]
        reprompt = data[prompts.FALLBACK_REPROMPT]
        handler_input.response_builder.speak(speech).ask(
            reprompt)
        return handler_input.response_builder.response


class LocalizationInterceptor(AbstractRequestInterceptor):
    """
    Add function to request attributes, that can load locale specific data.
    """

    def process(self, handler_input):
        locale = handler_input.request_envelope.request.locale
        logger.info("Locale is {}".format(locale))

        # localized strings stored in language_strings.json
        with open("language_strings.json") as language_prompts:
            language_data = json.load(language_prompts)
        # set default translation data to broader translation
        if locale[:2] in language_data:
            data = language_data[locale[:2]]
            # if a more specialized translation exists, then select it instead
            # example: "fr-CA" will pick "fr" translations first, but if "fr-CA" translation exists,
            # then pick that instead
            if locale in language_data:
                data.update(language_data[locale])
        else:
            data = language_data[locale]
        handler_input.attributes_manager.request_attributes["_"] = data


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In SessionEndedRequestHandler")

        logger.info("Session ended reason: {}".format(
            handler_input.request_envelope.request.reason))
        return handler_input.response_builder.response


# Exception Handler
class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler, log exception and
    respond with custom message.
    """

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.info("In CatchAllExceptionHandler")
        logger.error(exception, exc_info=True)

        handler_input.response_builder.speak(EXCEPTION_MESSAGE).ask(
            HELP_REPROMPT)

        return handler_input.response_builder.response


# Request and Response loggers
class RequestLogger(AbstractRequestInterceptor):
    """Log the alexa requests."""

    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.debug("Alexa Request: {}".format(
            handler_input.request_envelope.request))


class ResponseLogger(AbstractResponseInterceptor):
    """Log the alexa responses."""

    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.debug("Alexa Response: {}".format(response))


#stokes bay wind direction script

class WindHelper:
    @staticmethod
    def getWindDirection():

        windData = WindHelper.getWindData()
        windInDegrees = WindHelper.windDirectionFormatting(windData)

        if(windInDegrees < 0):
            return "ERROR"

        dirs = ["Northerly", "North north easterly", "North easterly", "East north easterly", "Easterly", "East south easterly", "South easterly", "South south easterly",
                "Southerly", "South south westerly", "South westerly", "West south westerly", "Westerly", "West north westerly", "North westerly", "North north westerly"]
        ix = int((windInDegrees + 11.25)/22.5)
        return dirs[ix % 16]


    @staticmethod
    def getWindData():
        url = "https://weatherfile.com/capi/V02/loc/GBR00074/latest.json"
        headers = {'wf-tkn':'PUBLIC'}

        response = requests.get(url,  headers=headers)
        json_data = response.json()

        return json_data

    @staticmethod
    def windDirectionFormatting(response):

        #error checking
        if "data" not in response:
            logger.info("Cant find 'data' key in json response")
            return -1
        elif not len(response["data"]):
            logger.info("Cant find dictionary inside 'data' key in json response")
            return -1
        elif "wdc" not in response["data"][0]:
            logger.info("Cant find 'WDC' key inside 'data' key in json response")
            return -1
        elif isinstance(response["data"][0]["wdc"],int) == False:
            logger.info("'WDC' key did not contain a float")
            return -1
        else:
            #print wind after converting
            num = response["data"][0]["wdc"]
            return(num)

    @staticmethod
    def getWindSpeed():
        response = WindHelper.getWindData()
        windSpeed = WindHelper.windSpeedFormatting(response)
        return windSpeed

    @staticmethod
    def windSpeedFormatting(response):
        #error checking
        if "data" not in response:
            logger.info("Cant find 'data' key in json response")
        elif not len(response["data"]):
            logger.info("Cant find dictionary inside 'data' key in json response")
        elif "wsc" not in response["data"][0]:
            logger.info("Cant find 'WSC' key inside 'data' key in json response")
        elif isinstance(response["data"][0]["wsc"],float) == False:
            logger.info("'WSC' key did not contain a float")
        else:
            #print wind after converting
            num = round(response["data"][0]["wsc"]*1.94384,2)
            return(num)

# Register intent handlers
sb.add_request_handler(GetWindDirectionHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Register exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# Register request and response interceptors
sb.add_global_request_interceptor(LocalizationInterceptor())
sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())

# Handler name that is used on AWS lambda
lambda_handler = sb.lambda_handler()
