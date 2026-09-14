! rule: S7.2-005
! covers: dummy-character
! evidence: effect
program type_parameters_assumed_dummy
    implicit none
    call check_length('AB', 2)
    call check_length('ABCDE', 5)
contains
    subroutine check_length(text, expected)
        character(len=*), intent(in) :: text
        integer, intent(in) :: expected
        if (len(text) /= expected) error stop 1
    end subroutine check_length
end program type_parameters_assumed_dummy
