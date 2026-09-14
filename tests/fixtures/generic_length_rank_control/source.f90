module generic_length_pair
    implicit none
    interface choose_length
        module procedure short_text, long_text
    end interface
contains
    subroutine short_text(value)
        character(len=1), intent(in) :: value
    end subroutine short_text
    subroutine long_text(value)
        character(len=2), intent(in) :: value(1)
    end subroutine long_text
end module generic_length_pair
