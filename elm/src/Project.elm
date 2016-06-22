module Project exposing (Model, Msg)

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

import DataTableGroup
import DataAnalysisScript

type alias Model = {
    id : Int,
    name : String,
    url : String,
    slug : String,
    description : String,
    group : String,
    group_members : Array String,
    creator : String,
    status : String,
    number_of_datasets : Int,
    data_table_groups : Array DataTableGroup.Model,
    analyses : Array DataAnalysisScript.Model,
    published : Bool,
    published_on : Date,
    date_created : Date
}

type Msg = Reset | New
