program i169e_cmplx_characteristics
  implicit none
  interface type_code
    procedure code_integer, code_real, code_complex
  end interface
  integer, parameter :: rk = selected_real_kind(10)
  complex :: defaulted
  complex(kind=rk) :: selected
  selected = cmplx(1.0_rk, 2.0_rk, kind=rk)
  defaulted = cmplx(-3)
  call require_true('cmplx result complex type', type_code(cmplx(1.0, 2.0)) == 3)
  call require_true('cmplx present kind selects complex kind', kind(cmplx(1.0_rk, 2.0_rk, kind=rk)) == rk)
  call require_true('cmplx absent kind default real kind', kind(cmplx(-3)) == kind(cmplx(0.0, 0.0)))
  write(*,'(a)') 'INTRINSICS 16.9.E CMPLX CHARACTERISTICS OK'
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
end program i169e_cmplx_characteristics
