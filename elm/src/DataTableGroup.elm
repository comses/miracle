module DataTableGroup exposing (Model, Msg)

import Date exposing (Date)
import Html exposing (Html, button, div, text)
import Html.App as App

type alias Model = {
    id : Int,
    name : String,
    url : String,
    slug : String,
    description : String,
    published : Bool,
    published_on : Date,
    date_created : Date
}

type Msg = Reset | New
