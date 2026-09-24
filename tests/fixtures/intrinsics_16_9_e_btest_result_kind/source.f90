program i169e_btest_result_kind
  implicit none
  integer, parameter :: alt_lk = merge(1, 4, kind(.false.) /= 1)
  call require_true('btest result default logical', &
      kind(btest(1, 0)) == kind(.false.) .and. alt_lk /= kind(.false.) .and. &
      kind(logical(btest(1, 0), kind=alt_lk)) == alt_lk)
  write(*,'(a)') 'INTRINSICS 16.9.E BTEST RESULT KIND OK'
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
end program i169e_btest_result_kind
