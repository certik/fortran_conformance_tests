module i169c_assoc_proc_cases_mod
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
  subroutine check_dummy(dummy)
    procedure(int_fun) :: dummy
    procedure(int_fun), pointer :: p
    p => dummy
    call require_true('dummy procedure ultimate argument true', associated(p, dummy))
    call require_false('dummy procedure wrong target false', associated(p, proc_b))
  end subroutine check_dummy

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
end module i169c_assoc_proc_cases_mod
program i169c_associated_proc_cases
  use i169c_assoc_proc_cases_mod
  implicit none
  procedure(int_fun), pointer :: p, q
  p => proc_a
  q => proc_a
  call require_true('same procedure target true', associated(p, proc_a))
  call require_false('different procedure target false', associated(p, proc_b))
  call require_true('procedure pointer same procedure true', associated(p, q))
  q => proc_b
  call require_false('procedure pointer different procedure false', associated(p, q))
  call check_dummy(proc_a)
  write(*,'(a)') 'INTRINSICS 16.9.C ASSOCIATED PROC CASES OK'
end program i169c_associated_proc_cases
