module DataTableGroup exposing (init, view, update, Model, toRawDataTableGroup, fromRawDataTableGroup, Msg(..))

import Html exposing (..)
import Html.App as App
import Html.Attributes exposing (type', value, class, classList)
import Html.Events exposing (onClick, onInput)

import Platform.Cmd as Cmd

import IntDict
import Array

import Http
import Task

import Api.DataTableGroup

import DataColumn as Column exposing (fromColumn)
import Cancelable exposing (toCancelable, fromCancelable)
import Raw exposing (DataTableGroup, columnEx)
import StyledNodes as SN

type alias Model = 
    { id: Int
    , name: String 
    , full_name: Cancelable.Model String
    , description: Cancelable.Model String
    , project: String
    , url: String
    , number_of_files: Int
    , number_of_columns: Int
    , indexed_columns: IntDict.IntDict Column.Model
    , dirty: Bool
    , warning: String
    , loading: Bool
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
        Array.fromList (List.map Column.toColumn (IntDict.values model.indexed_columns))
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
    , indexed_columns = IntDict.fromList  (Array.toIndexedList (Array.map Column.fromColumn datatablegroup.columns))
    , dirty = False
    , warning = ""
    , loading = True
    }


type Msg 
    = FullName (Cancelable.Msg String)
    | Description (Cancelable.Msg String)
    | Modify Int Column.Msg 
    | Reset
    | Dirty
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
    , indexed_columns=IntDict.fromList [
        (0
        , Column.fromColumn columnEx
        ),
        (1
        , Column.fromColumn { columnEx | id = 1}
        )]
    , dirty = False
    , warning = ""
    , loading = True
    }, get id)


update: Msg -> Model -> (Model, Cmd Msg)
update msg model =
    case msg of
        FullName msg -> ({ model | full_name = Cancelable.update msg model.full_name }, Cmd.none)

        Description msg -> ({ model | description = Cancelable.update msg model.description }, Cmd.none)

        Modify id col_msg ->
            let column = IntDict.get id model.indexed_columns
                val =  Maybe.map (Column.update col_msg) column
            in case val of

                Just (column', col_msg') ->
                        ({ model | indexed_columns
                                = IntDict.update id (always (Just column')) model.indexed_columns }, Cmd.map (Modify id) col_msg')

                Nothing -> (model, Cmd.none)

        Reset -> ({ model | dirty = False
                          , full_name = Cancelable.update Cancelable.Reset model.full_name
                          , description = Cancelable.update Cancelable.Reset model.description }, Cmd.none)

        Dirty -> ({ model | dirty = True }, Cmd.none)

        Set -> (model, set model)

        Get id -> (model, get id)

        FetchSucceed raw_datatablegroup ->
            let model' = fromRawDataTableGroup raw_datatablegroup
            in ({ model' | loading = False }, Cmd.none)

        FetchFail error -> ({ model | warning = toString error }, Cmd.none)


view: Model -> Html Msg
view model =
    let btnClass = classList
            [ ("btn btn-primary", True)
            , ("hidden", not model.dirty)
            ]
    in if not model.loading then
        div [ class "panel panel-primary" ]
            [ div [ class "panel-heading" ]
                [ text "DataGroup: "
                , i []
                    [ text ("(" ++ model.name ++ ")")
                , text " Files: "
                , span [ class "label label-badge label-default" ] [ text (toString model.number_of_files) ]
                , text " Columns: "
                , span [ class "label label-badge label-default" ] [ text (toString model.number_of_columns) ]
                ]
            ]
            , div [ class "panel-body" ]
                [ form [ class "form form-horizontal", onInput (\_ -> Dirty) ]
                    [ viewFullName model
                    , input [ type' "button", onClick Set, btnClass, value "Save"] []
                    , input [ type' "button", onClick Reset, btnClass, value "Cancel"] []
                    ]
                , div [ class "panel panel-default" ]
                    [ div [ class "panel-heading" ] [ text "Columns" ]
                    , div [ class "panel-body" ]
                        (List.intersperse (hr [] []) (List.map viewColumn (IntDict.toList model.indexed_columns)))
                    ]
                ]
            ]
    else
        text "Loading"


viewFullName: Model -> Html Msg
viewFullName model = App.map FullName
    (Cancelable.viewTextField (onInput (always Cancelable.Dirty)) model.full_name (text "Full Name"))


viewColumn: (Int, Column.Model) -> Html Msg
viewColumn (id, model) =
    App.map (Modify id) (Column.view model)


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


main = App.program { init = init { id=4 }, update = update, view = view, subscriptions = \_ -> Sub.none }
