module Parameter exposing (..)

import Http
import Task

import Raw

type alias Model = Raw.Parameter

toRawParameter: Model -> Raw.Parameter
toRawParameter = identity

fromRawParameter: Raw.Parameter
fromRawParmeter = identity

