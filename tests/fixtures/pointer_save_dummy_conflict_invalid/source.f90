module save_dummy_conflict_mod
contains
  subroutine takes_saved_dummy(x)
    implicit none
    integer, intent(in) :: x
    save :: x
  end subroutine takes_saved_dummy
end module save_dummy_conflict_mod
