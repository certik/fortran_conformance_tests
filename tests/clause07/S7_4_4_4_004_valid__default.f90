! rule: S7.4.4.4-004
! covers: default-ascii-order
! evidence: effect
! standard: f2023
program character_type_case
    implicit none
    call check(lge('ONE','TWO'), .false.)
    call check(lgt('ONE','TWO'), .false.)
    call check(lle('ONE','TWO'), .true.)
    call check(llt('ONE','TWO'), .true.)
    call check(lge('TWO','ONE'), .true.)
    call check(lgt('TWO','ONE'), .true.)
    call check(lle('TWO','ONE'), .false.)
    call check(llt('TWO','ONE'), .false.)
    call check(lge('ONE','ONE'), .true.)
    call check(lgt('ONE','ONE'), .false.)
    call check(lle('ONE','ONE'), .true.)
    call check(llt('ONE','ONE'), .false.)
contains
    subroutine check(value, expected)
        logical, intent(in) :: value, expected
        if (value .neqv. expected) error stop 1
    end subroutine
end program
