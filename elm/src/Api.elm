module Api exposing (..)

import Http
import Json.Decode as Json exposing ((:=))

import Hop exposing (..)
import Hop.Matchers exposing (match1, match2, int, str)
import Hop.Types exposing (Config, Query, Location, PathMatcher, Router)

import Task

import Csrf
import Raw

import DataColumn exposing (fromColumn, toColumn)
import DataTableGroup exposing (fromDataTableGroup, toDataTableGroup)


-- TODO: convert API to use routes
-- Routes

type Route
    = DashboardRoute
    | ProjectRoute String
    | ProjectListRoute
    | NotFound


dashboardMatcher : PathMatcher Route
dashboardMatcher =
    match1 DashboardRoute "/dashboard"

projectMatcher : PathMatcher Route
projectMatcher =
    match2 ProjectRoute "/projects/" str

projectListMatcher : PathMatcher Route
projectListMatcher =
    match1 ProjectListRoute "/projects/"

reverse : Route -> String
reverse route =
    case route of

        DashboardRoute ->
            matcherToPath dashboardMatcher []

        ProjectRoute slug ->
            matcherToPath projectMatcher [slug]

        ProjectListRoute ->
            matcherToPath projectListMatcher []

        NotFound -> 
            ""
