subroutine local_route()
    implicit none
    character(3), external :: character_external
    character(3) :: text
    text = character_external(3)
    if (text /= 'ABC') error stop 2
end subroutine
subroutine host_route()
    implicit none
    character(3), external :: character_external
    call inner()
contains
    subroutine inner()
        character(3) :: text
        text = character_external(3)
        if (text /= 'ABC') error stop 3
    end subroutine
end subroutine
subroutine use_route()
    use character_declarations, only: character_external
    implicit none
    character(3) :: text
    text = character_external(3)
    if (text /= 'ABC') error stop 4
end subroutine
subroutine dummy_route(f)
    implicit none
    character(3), external :: f
    character(3) :: text
    text = f(3)
    if (text /= 'ABC') error stop 5
    call forwarded(f)
end subroutine
subroutine forwarded(f)
    implicit none
    character(3), external :: f
    character(3) :: text
    text = f(3)
    if (text /= 'ABC') error stop 6
end subroutine
