program i169p_lgt_result_kind
  implicit none
  integer, parameter :: alt_lk = merge(1, 4, kind(.false.) /= 1)
  call require_true('lgt result default logical kind', kind(lgt('A', '9')) == kind(.false.))
  write(*,'(a)') 'INTRINSICS 16.9.P LGT RESULT KIND OK'
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
end program i169p_lgt_result_kind
