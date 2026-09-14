! rule: R701
! covers: scalar-integer-expression
! evidence: positive-control
program type_parameters_expression
    implicit none
    call check_length(2, 3)
    call check_length(4, 5)
contains
    subroutine check_length(n, expected)
        integer, intent(in) :: n, expected
        character(len=n+1) :: text

        if (len(text) /= expected) error stop 1
        text = repeat('A', expected)
        if (text /= repeat('A', expected)) error stop 2
    end subroutine check_length
end program type_parameters_expression
