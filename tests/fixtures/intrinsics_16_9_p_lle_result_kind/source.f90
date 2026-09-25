program i169p_lle_result_kind
  implicit none
  integer, parameter :: alt_lk = merge(1, 4, kind(.false.) /= 1)
  call require_true('lle result default logical kind', kind(lle('9', 'A')) == kind(.false.))
  write(*,'(a)') 'INTRINSICS 16.9.P LLE RESULT KIND OK'
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
end program i169p_lle_result_kind
