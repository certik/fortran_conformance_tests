program p
    implicit none
    character(3), external :: character_external
    call local_route()
    call host_route()
    call use_route()
    call dummy_route(character_external)
end program
