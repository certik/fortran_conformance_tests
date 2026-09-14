! rule: S7.2-002
! covers: character-length-integer-name
! evidence: effect
program type_parameters_len_name
    implicit none
    character(len=3) :: text = 'ABC'
    integer, parameter :: length_kind = kind(text%len)

    call check_length(text%len)
    if (text%len /= len(text)) error stop 2
contains
    subroutine check_length(value)
        integer(kind=length_kind), intent(in) :: value
        if (value /= 3) error stop 1
    end subroutine check_length
end program type_parameters_len_name
