program i169e_ceiling_exact
  implicit none
  interface type_code
    procedure code_integer, code_real, code_complex
  end interface
  integer, parameter :: ik = selected_int_kind(12)
  real :: a
  integer(kind=ik) :: wide
  integer :: defaulted
  a = 3.25
  wide = ceiling(a, kind=ik)
  defaulted = ceiling(-3.25)
  call require_true('ceiling real argument exact positive', ceiling(a) == 4)
  call require_true('ceiling result integer type', type_code(ceiling(a)) == 1)
  call require_true('ceiling kind scalar constant selects kind', kind(ceiling(a, kind=ik)) == ik .and. wide == 4_ik)
  call require_true('ceiling default integer kind absent', kind(ceiling(-3.25)) == kind(0))
  call require_true('ceiling least integer negative', defaulted == -3)
  call require_true('ceiling integral value unchanged', ceiling(3.0) == 3)
  write(*,'(a)') 'INTRINSICS 16.9.E CEILING VALUES OK'
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
  integer function code_integer(x)
    integer, intent(in) :: x
    code_integer = 1
  end function code_integer
  integer function code_real(x)
    real, intent(in) :: x
    code_real = 2
  end function code_real
  integer function code_complex(x)
    complex, intent(in) :: x
    code_complex = 3
  end function code_complex
end program i169e_ceiling_exact
