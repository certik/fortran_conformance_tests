program i169e_bge_result_kind
  implicit none
  integer, parameter :: alt_lk = merge(1, 4, kind(.false.) /= 1)
  logical :: observed
  observed = bge(z'80000000', 1)
  call require_true('bge true bit-sequence comparison', observed)
  observed = bge(1, z'80000000')
  call require_false('bge false bit-sequence comparison', observed)
  call require_true('bge result default logical', &
      kind(bge(1, 1)) == kind(.false.) .and. alt_lk /= kind(.false.) .and. &
      kind(logical(bge(1, 1), kind=alt_lk)) == alt_lk)
  write(*,'(a)') 'INTRINSICS 16.9.E BGE RESULT KIND OK'
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
end program i169e_bge_result_kind
