program p
    implicit none
    call short_path()
    call long_path()
contains
    subroutine short_path()
        character(2), external :: character_external
        character(2) :: text
        text = character_external(2)
        if (len(character_external(2)) /= 2) error stop 2
        if (text /= 'AB') error stop 3
    end subroutine
    subroutine long_path()
        character(5), external :: character_external
        character(5) :: text
        text = character_external(5)
        if (len(character_external(5)) /= 5) error stop 4
        if (text /= 'ABCDE') error stop 5
    end subroutine
end program
