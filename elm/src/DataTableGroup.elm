module DataTableGroup exposing (..)

import Html exposing (..)
import Html.App as App
import Html.Attributes exposing (type', value, class, classList, style, attribute)
import Html.Events exposing (onClick, onInput)

import Platform.Cmd as Cmd

import IntDict
import Array

import Http
import Task

import Api.DataTableGroup

import ArrayComponent
import DataColumn as Column exposing (fromColumn)
import Cancelable exposing (toCancelable, fromCancelable)
import Raw exposing (DataTableGroup, columnEx)
import Util


type alias Model = 
    { id: Int
    , name: String 
    , full_name: Cancelable.Model String
    , description: Cancelable.Model String
    , project: String
    , url: String
    , number_of_files: Int
    , number_of_columns: Int
    , columns: Array.Array Column.Model
    , dirty: Bool
    , warning: String
    , expanded: Bool
    }


toRawDataTableGroup: Model -> DataTableGroup
toRawDataTableGroup model =
    { id=model.id
    , name=model.name
    , full_name= fromCancelable model.full_name
    , description= fromCancelable model.description
    , project= model.project
    , url= model.url
    , number_of_files= model.number_of_files
    , number_of_columns= model.number_of_columns
    , columns =
        Array.map Column.toColumn model.columns
    }


fromRawDataTableGroup: DataTableGroup -> Model
fromRawDataTableGroup datatablegroup =
    { id= datatablegroup.id
    , name= datatablegroup.name
    , full_name= toCancelable datatablegroup.full_name
    , description= toCancelable datatablegroup.description
    , project= datatablegroup.project
    , url = datatablegroup.url
    , number_of_files= datatablegroup.number_of_files
    , number_of_columns = datatablegroup.number_of_columns
    , columns = Array.map Column.fromColumn datatablegroup.columns
    , dirty = False
    , warning = ""
    , expanded = False
    }


type Msg 
    = FullName (Cancelable.Msg String)
    | Description (Cancelable.Msg String)
    | Modify Int Column.Msg 
    | Reset
    | Dirty
    | Expand
    | Get Int
    | Set
    | FetchSucceed Raw.DataTableGroup
    | FetchFail String


init: {id: Int} -> (Model, Cmd Msg)
init {id} =
    ({ id=0
    , name=""
    , full_name= toCancelable ""
    , description= toCancelable ""
    , project=""
    , url=""
    , number_of_files= 0
    , number_of_columns= 0
    , columns=Array.fromList
        [ Column.fromColumn columnEx
        , Column.fromColumn { columnEx | id = 1}
        ]
    , dirty = False
    , warning = ""
    , expanded = True
    }, get id)


updateColumns:
    Int -> Column.Msg -> Array.Array Column.Model -> (Array.Array Column.Model, Cmd Msg)
updateColumns =
    ArrayComponent.updateChild Modify Column.update


update: Msg -> Model -> (Model, Cmd Msg)
update msg model =
    case msg of
        FullName msg -> ({ model | full_name = Cancelable.update msg model.full_name }, Cmd.none)

        Description msg -> ({ model | description = Cancelable.update msg model.description }, Cmd.none)

        Modify id col_msg ->
              let (columns, msg') = updateColumns id col_msg model.columns
              in ({ model | columns = columns }, msg')

        Reset -> ({ model | dirty = False
                          , full_name = Cancelable.update Cancelable.Reset model.full_name
                          , description = Cancelable.update Cancelable.Reset model.description }, Cmd.none)

        Dirty -> ({ model | dirty = True }, Cmd.none)

        Expand -> ({ model | expanded = not model.expanded }, Cmd.none)

        Set -> (model, set model)

        Get id -> (model, get id)

        FetchSucceed raw_datatablegroup ->
            let model' = fromRawDataTableGroup raw_datatablegroup
            in ( model', Cmd.none)

        FetchFail error -> ({ model | warning = toString error }, Cmd.none)


view: Html Msg -> Model -> Html Msg
view subview model =
    div [ class "panel panel-default", lessPadding ]
        [ div [ class "panel-heading", onClick Expand ]
            [ text (Cancelable.fromCancelable model.full_name)
            , i []
                [ text (" (" ++ model.name ++ ")") ]
            ]
        , subview
        ]

viewForm: Model -> Html Msg
viewForm model =
    if model.expanded then
        form [ class "form form-horizontal", Util.onChange Dirty ]
            [ viewFullName model
            , viewDescription model
            , div
                [ class "form-group" ]
                [ div
                    [ class "col-xs-offset-2 btn-group btn-group-sm" ]
                    [ button
                        [ onClick Set, class "btn btn-primary" ]
                        [ span [ class "fa fa-floppy-o", attribute "aria-hidden" "true" ] [ ] ]
                    , button
                        [ onClick Reset, class "btn btn-primary" ]
                        [ span [ class "fa fa-undo", attribute "aria-hidden" "true" ] [ ]]
                    ]
                ]
            ]
    else
        div [ class "hidden" ] []


viewFullName: Model -> Html Msg
viewFullName model = App.map FullName
    (Cancelable.viewTextField (Util.onChange Cancelable.Dirty) model.full_name (text "Full Name"))


viewDescription: Model -> Html Msg
viewDescription model = App.map Description
    (Cancelable.viewTextArea (Util.onChange Cancelable.Dirty) model.description (text "Description"))


viewTableRows: Model -> Html Msg
viewTableRows model =
    if model.expanded then
        table
            [ class "table table-bordered table-condensed" ]
            [ thead
                [ ]
                [ tr
                    []
                    [ th [] [ text "Name" ]
                    , th [] [ text "Full Name" ]
                    , th [] [ text "Data Type" ]
                    , th [] [ text "Description" ]
                    ]
                ]
            , tbody
                [ ]
                (viewColumnsTableRow model)
            ]
    else div [] []



lessPadding = style
    [ ("padding", "0px 0px")]


viewColumnsTableRow: Model -> List (Html Msg)
viewColumnsTableRow model = ArrayComponent.viewList Modify Column.viewTableRow model.columns


get: Int -> Cmd Msg
get id =
    Task.perform
        (toString >> FetchFail)
        FetchSucceed
        (Api.DataTableGroup.getTask id |> (Http.fromJson Raw.datatablegroupDecoder))


set: Model -> Cmd Msg
set model =
    Task.perform
        (toString >> FetchFail)
        FetchSucceed
        (Api.DataTableGroup.setTask (toRawDataTableGroup model) |> (Http.fromJson Raw.datatablegroupDecoder))
