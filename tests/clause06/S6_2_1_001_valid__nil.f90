! rule: S6.2.1-001
! covers: nil
! evidence: positive-control
! standard: f2023
program token_nil_admission
    implicit none
    logical :: choose

    choose = .true.
    call check_optional((choose ? 37 : .NIL.), .true.)
    choose = .false.
    call check_optional((choose ? 37 : .NIL.), .false.)
contains
    subroutine check_optional(value, expected)
        integer, optional, intent(in) :: value
        logical, intent(in) :: expected

        if (present(value) .neqv. expected) error stop 1
        if (present(value)) then
            if (value /= 37) error stop 2
        end if
    end subroutine check_optional
end program token_nil_admission
