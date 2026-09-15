! rule: S7.4.4.4-004
! covers: padding-and-empty
! evidence: effect
! standard: f2023
program character_type_case
    implicit none
    call equal('A', 'A  ')
    call equal('A  ', 'A')
    call equal('', '   ')
    call equal('   ', '')
    call equal('', '')
    if (.not. llt('ONEZ', 'TWOA')) error stop 1
    if (lge('ONEZ', 'TWOA')) error stop 2
    if (.not. lgt('TWOA', 'ONEZ')) error stop 3
    if (lle('TWOA', 'ONEZ')) error stop 4
contains
    subroutine equal(a, b)
        character(*), intent(in) :: a, b
        if (.not. lge(a,b) .or. .not. lle(a,b)) error stop 5
        if (lgt(a,b) .or. llt(a,b)) error stop 6
    end subroutine
end program
