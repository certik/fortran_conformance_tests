program i169p_leadz_result_kind
  implicit none
  integer, parameter :: alt_ik = merge(8, 4, kind(0) /= 8)
  integer :: one
  one = 1
  call require_true('leadz result default integer kind', kind(leadz(one)) == kind(0))
  write(*,'(a)') 'INTRINSICS 16.9.P LEADZ RESULT KIND OK'
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
end program i169p_leadz_result_kind
