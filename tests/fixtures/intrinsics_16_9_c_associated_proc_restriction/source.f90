module i169c_assoc_proc_restriction_mod
  implicit none
  abstract interface
    integer function int_fun(x)
      integer, intent(in) :: x
    end function int_fun
  end interface
contains
  integer function proc_a(x)
    integer, intent(in) :: x
    proc_a = x + 1
  end function proc_a
  integer function proc_b(x)
    integer, intent(in) :: x
    proc_b = x + 2
  end function proc_b
end module i169c_assoc_proc_restriction_mod
program i169c_associated_proc_restriction
  use i169c_assoc_proc_restriction_mod
  implicit none
  procedure(int_fun), pointer :: p, q
  p => proc_a
  q => proc_b
  call require_true('allowable procedure target true', associated(p, proc_a))
  call require_true('same characteristics procedure target true', associated(q, proc_b))
  call require_false('same characteristics wrong procedure false', associated(p, proc_b))
  write(*,'(a)') 'INTRINSICS 16.9.C ASSOCIATED PROC RESTRICTION OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_false(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_false
end program i169c_associated_proc_restriction
