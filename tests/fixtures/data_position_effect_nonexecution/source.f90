program data_position_nonexecution_effect
  implicit none
  integer :: observed, entries, before_returns, returns, body_checks, after_data, checks
  observed=-1
  entries=0
  before_returns=0
  returns=0
  body_checks=0
  after_data=0
  checks=0
  observed=read_kept()
  returns=returns+1
  if (entries /= 1) then
    write(*,'(a)') 'DPE:nonexecution:function-entries'
    error stop
  end if
  checks=checks+1
  if (before_returns /= 1) then
    write(*,'(a)') 'DPE:nonexecution:before-return-events'
    error stop
  end if
  checks=checks+1
  if (returns /= 1) then
    write(*,'(a)') 'DPE:nonexecution:normal-returns'
    error stop
  end if
  checks=checks+1
  if (body_checks /= 1) then
    write(*,'(a)') 'DPE:nonexecution:body-checks'
    error stop
  end if
  checks=checks+1
  if (observed /= 7) then
    write(*,'(a)') 'DPE:nonexecution:returned-value'
    error stop
  end if
  checks=checks+1
  if (after_data /= 0) then
    write(*,'(a)') 'DPE:nonexecution:after-data-events'
    error stop
  end if
  checks=checks+1
  if (checks /= 6) then
    write(*,'(a)') 'DPE:nonexecution:check-total'
    error stop
  end if
  write(*,'(a)') 'DATA POSITION NONEXECUTION OK'
contains
  integer function read_kept() result(value)
    implicit none
    integer :: kept
    entries=entries+1
    if (kept /= 7) then
      write(*,'(a)') 'DPE:nonexecution:local-initial-value'
      error stop
    end if
    body_checks=body_checks+1
    value=kept
    before_returns=before_returns+1
    return
    data kept /7/
    after_data=after_data+1
  end function read_kept
end program data_position_nonexecution_effect
