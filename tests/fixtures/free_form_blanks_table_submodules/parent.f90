module blank_parent
  implicit none
  interface
    module subroutine set_one(value)
      integer, intent(out) :: value
    end subroutine
    module subroutine set_two(value)
      integer, intent(out) :: value
    end subroutine
  end interface
end module
