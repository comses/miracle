module Metadata exposing (Model, Msg)

{-| Model for Projects

# the Project Model
@docs Model 


# message types
@docs Msg
-}

import Array exposing (Array)
import Date exposing (Date)
import Html exposing (Html, button, div, text)
import Html.App as App

import Json.Decode as Decode exposing ((:=))
import Json.Encode as Encode

import DataTableGroup
import DataAnalysisScript

import Http
import Task

type alias Model =
    { id : Int
--    , name : String
--    , url : String
    , slug : String
--    , description : String
--    , group : String
--    , group_members : Array String
--    , creator : String
--    , status : String
--    , number_of_datasets : Int
--    , data_table_groups : Array DataTableGroup.Model
--    , analyses : Array DataAnalysisScript.Model
--    , published : Bool
--    , published_on : Date
--    , date_created : Date
    }

metadataDecoder: Decode.Decoder Model
metadataDecoder =
    Decode.object2
    ("id" := Decode.int)
    ("slug" := Decode.string)
--    ("data_table_groups" := Array DataTableGroup.Model)

metadataEncoder: Model -> Encode.Value
metadataEncoder model =
    Encode.object
    [ ("id", Encode.int model.id)
    , ("slug", Encode.string model.slug)]

type Msg = Get String


empty: Model
empty = { id = -1, slug = ""}


init: (Model, Cmd Msg)
init = (empty, getModel)


getModel: Task Http.Error Model
getModel = Http.get