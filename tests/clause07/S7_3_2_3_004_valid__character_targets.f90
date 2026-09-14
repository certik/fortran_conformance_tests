! rule: S7.3.2.3-004
! covers: unlimited-character-targets
! evidence: effect
program dynamic_character_targets
    implicit none
    character(len=3), target :: short_text = 'elm'
    character(len=5), target :: long_text = 'cedar'
    class(*), pointer :: p => null()
    p => short_text
    if (.not. associated(p)) error stop 'short-association'
    select type (p)
    type is (character(len=*))
        if (len(p) /= 3) error stop 'short-length'
        if (p /= 'elm') error stop 'short-payload'
    class default
        error stop 'short-dynamic-type'
    end select
    p => long_text
    if (.not. associated(p)) error stop 'long-association'
    select type (p)
    type is (character(len=*))
        if (len(p) /= 5) error stop 'long-length'
        if (p /= 'cedar') error stop 'long-payload'
    class default
        error stop 'long-dynamic-type'
    end select
    nullify(p)
end program
