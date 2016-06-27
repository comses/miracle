module DataTableGroup exposing (init, view, update, Model, toRawDataTableGroup, fromRawDataTableGroup, Msg(..))

import Html exposing (..)
import Html.App as App
import Html.Attributes exposing (type', value, class)
import Html.Events exposing (onClick)

import Platform.Cmd as Cmd

import IntDict
import Array

import Http
import Task

import Api.DataTableGroup

import DataColumn as Column exposing (fromColumn)
import Cancelable exposing (toCancelable, fromCancelable)
import Raw exposing (DataTableGroup, columnEx)


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
    div []
        [ h4 []
            [ text "DataGroup: "
            , form [ class "form form-horizontal" ]
                [ viewTextField model.full_name
                , input [ type' "button", onClick Set, class "btn", value "Save"] []
                , input [ type' "button", onClick Reset, class "btn", value "Cancel"] []
                , i [] [text (" " ++ model.name) ]
                ]
            ]
        , if not model.loading then
            div [] (List.map viewColumn (IntDict.toList model.indexed_columns))
          else text "Loading"
        ] 


viewTextField: Cancelable.Model String -> Html Msg
viewTextField model = App.map FullName (Cancelable.viewTextField model "Full Name")


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


rawStr = """{"id":1,"name":"runLog","full_name":"","description":"","project":"luxedemo","url":"https://localhost/data-group/1.json","columns":[{"id":1,"data_table_group":"runLog","name":"runID","full_name":"","description":"","data_type":"bigint","table_order":1},{"id":2,"data_table_group":"runLog","name":"random","full_name":"","description":"","data_type":"bigint","table_order":2},{"id":3,"data_table_group":"runLog","name":"runNumber","full_name":"","description":"","data_type":"bigint","table_order":3},{"id":4,"data_table_group":"runLog","name":"msgOutLevel","full_name":"","description":"","data_type":"bigint","table_order":4},{"id":5,"data_table_group":"runLog","name":"worldx","full_name":"","description":"","data_type":"bigint","table_order":5},{"id":6,"data_table_group":"runLog","name":"worldy","full_name":"","description":"","data_type":"bigint","table_order":6},{"id":7,"data_table_group":"runLog","name":"centerx","full_name":"","description":"","data_type":"bigint","table_order":7},{"id":8,"data_table_group":"runLog","name":"centery","full_name":"","description":"","data_type":"bigint","table_order":8},{"id":9,"data_table_group":"runLog","name":"buyer","full_name":"","description":"","data_type":"bigint","table_order":9},{"id":10,"data_table_group":"runLog","name":"seller","full_name":"","description":"","data_type":"bigint","table_order":10},{"id":11,"data_table_group":"runLog","name":"maxBiddingTries","full_name":"","description":"","data_type":"bigint","table_order":11},{"id":12,"data_table_group":"runLog","name":"unitTransportCost","full_name":"","description":"","data_type":"bigint","table_order":12},{"id":13,"data_table_group":"runLog","name":"neighborhoodSize","full_name":"","description":"","data_type":"bigint","table_order":13},{"id":14,"data_table_group":"runLog","name":"budget","full_name":"","description":"","data_type":"bigint","table_order":14},{"id":15,"data_table_group":"runLog","name":"sdbudget","full_name":"","description":"","data_type":"bigint","table_order":15},{"id":16,"data_table_group":"runLog","name":"search","full_name":"","description":"","data_type":"bigint","table_order":16},{"id":17,"data_table_group":"runLog","name":"bid","full_name":"","description":"","data_type":"bigint","table_order":17},{"id":18,"data_table_group":"runLog","name":"agr","full_name":"","description":"","data_type":"bigint","table_order":18},{"id":19,"data_table_group":"runLog","name":"util","full_name":"","description":"","data_type":"decimal","table_order":19},{"id":20,"data_table_group":"runLog","name":"sdp","full_name":"","description":"","data_type":"decimal","table_order":20},{"id":21,"data_table_group":"runLog","name":"range","full_name":"","description":"","data_type":"decimal","table_order":21},{"id":22,"data_table_group":"runLog","name":"steps","full_name":"","description":"","data_type":"bigint","table_order":22},{"id":23,"data_table_group":"runLog","name":"luFile","full_name":"","description":"","data_type":"text","table_order":23},{"id":24,"data_table_group":"runLog","name":"tpFile","full_name":"","description":"","data_type":"text","table_order":24},{"id":25,"data_table_group":"runLog","name":"lufile2","full_name":"","description":"","data_type":"text","table_order":25},{"id":26,"data_table_group":"runLog","name":"tpFile2","full_name":"","description":"","data_type":"text","table_order":26},{"id":27,"data_table_group":"runLog","name":"agents","full_name":"","description":"","data_type":"text","table_order":27}],"number_of_files":1,"number_of_columns":27}"""


main = App.program { init = init { id=4 }, update = update, view = view, subscriptions = \_ -> Sub.none }
