! rule: S7.2-003
! covers: character-length-invariance
! evidence: effect
module type_parameters_character_generic
    implicit none
    interface measure
        module procedure character_length
    end interface
contains
    integer function character_length(value) result(length)
        character(len=*), intent(in) :: value
        length = len(value)
    end function character_length
end module type_parameters_character_generic

program type_parameters_length_dispatch
    use type_parameters_character_generic, only: measure
    implicit none
    if (measure('AB') /= 2) error stop 1
    if (measure('ABCDE') /= 5) error stop 2
end program type_parameters_length_dispatch
