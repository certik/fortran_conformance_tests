! rule: S7.2-005
! covers: select-type-character
! evidence: effect
program type_parameters_assumed_selector
    implicit none
    call check_length('AB', 2)
    call check_length('ABCDE', 5)
contains
    subroutine check_length(value, expected)
        class(*), intent(in) :: value
        integer, intent(in) :: expected

        select type (text => value)
        type is (character(len=*))
            if (len(text) /= expected) error stop 1
        class default
            error stop 2
        end select
    end subroutine check_length
end program type_parameters_assumed_selector
