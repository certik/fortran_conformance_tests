program i169i_exponent_result_kind
  implicit none
  integer, parameter :: alt_int_kind = merge(8, 4, kind(0) /= 8)
  integer, parameter :: result_power = 2
  real :: result_x
  result_x = real(radix(1.0), kind(1.0)) ** result_power
  call require_true('exponent result default integer', kind(exponent(result_x)) == kind(0))
  write(*,'(a)') 'INTRINSICS 16.9.I EXPONENT RESULT KIND OK'
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
end program i169i_exponent_result_kind
