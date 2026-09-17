program explicit_block_bounds
  implicit none
  integer :: n, visit, outer_upper, outer_extent, outer_value
  integer :: inner_bound, inner_upper, inner_extent, inner_value
  integer :: outer_entries, inner_entries, inner_exits, outer_exits, events, checks
  outer_entries=0
  inner_entries=0
  inner_exits=0
  outer_exits=0
  events=0
  checks=0
  do visit=1,2
    if (visit == 1) then
      n=3
      outer_upper=3
      outer_extent=6
      outer_value=201
      inner_bound=5
      inner_upper=5
      inner_extent=5
      inner_value=301
    else
      n=1
      outer_upper=1
      outer_extent=4
      outer_value=202
      inner_bound=2
      inner_upper=2
      inner_extent=2
      inner_value=302
    end if
    outer_activation: block
      integer :: outer(-2:n)
      outer=200+visit
      outer_entries=outer_entries+1
      events=events+1
      if (outer_entries /= visit) then
        write(*,'(a,i1)') 'EBC:outer-entry:activation=', visit
        error stop 'EBC:outer-entry'
      end if
      checks=checks+1
      if (events /= 6*(visit-1)+1) then
        write(*,'(a,i1)') 'EBC:outer-entry-event:activation=', visit
        error stop 'EBC:outer-entry-event'
      end if
      checks=checks+1
      if (lbound(outer,1) /= -2) then
        write(*,'(a,i1)') 'EBC:outer-initial-lower:activation=', visit
        error stop 'EBC:outer-initial-lower'
      end if
      checks=checks+1
      if (ubound(outer,1) /= outer_upper) then
        write(*,'(a,i1)') 'EBC:outer-initial-upper:activation=', visit
        error stop 'EBC:outer-initial-upper'
      end if
      checks=checks+1
      if (size(outer) /= outer_extent) then
        write(*,'(a,i1)') 'EBC:outer-initial-size:activation=', visit
        error stop 'EBC:outer-initial-size'
      end if
      checks=checks+1
      if (any(shape(outer) /= [outer_extent])) then
        write(*,'(a,i1)') 'EBC:outer-initial-shape:activation=', visit
        error stop 'EBC:outer-initial-shape'
      end if
      checks=checks+1
      if (any(outer /= outer_value)) then
        write(*,'(a,i1)') 'EBC:outer-initial-values:activation=', visit
        error stop 'EBC:outer-initial-values'
      end if
      checks=checks+1
      n=inner_bound
      events=events+1
      if (n /= inner_upper) then
        write(*,'(a,i1)') 'EBC:outer-source-redefined:activation=', visit
        error stop 'EBC:outer-source-redefined'
      end if
      checks=checks+1
      if (events /= 6*(visit-1)+2) then
        write(*,'(a,i1)') 'EBC:outer-redefinition-event:activation=', visit
        error stop 'EBC:outer-redefinition-event'
      end if
      checks=checks+1
      if (lbound(outer,1) /= -2) then
        write(*,'(a,i1)') 'EBC:outer-redefined-lower:activation=', visit
        error stop 'EBC:outer-redefined-lower'
      end if
      checks=checks+1
      if (ubound(outer,1) /= outer_upper) then
        write(*,'(a,i1)') 'EBC:outer-redefined-upper:activation=', visit
        error stop 'EBC:outer-redefined-upper'
      end if
      checks=checks+1
      if (size(outer) /= outer_extent) then
        write(*,'(a,i1)') 'EBC:outer-redefined-size:activation=', visit
        error stop 'EBC:outer-redefined-size'
      end if
      checks=checks+1
      if (any(shape(outer) /= [outer_extent])) then
        write(*,'(a,i1)') 'EBC:outer-redefined-shape:activation=', visit
        error stop 'EBC:outer-redefined-shape'
      end if
      checks=checks+1
      if (any(outer /= outer_value)) then
        write(*,'(a,i1)') 'EBC:outer-redefined-values:activation=', visit
        error stop 'EBC:outer-redefined-values'
      end if
      checks=checks+1
      inner_activation: block
        integer :: inner(1:n)
        inner=300+visit
        inner_entries=inner_entries+1
        events=events+1
        if (inner_entries /= visit) then
          write(*,'(a,i1)') 'EBC:inner-entry:activation=', visit
          error stop 'EBC:inner-entry'
        end if
        checks=checks+1
        if (events /= 6*(visit-1)+3) then
          write(*,'(a,i1)') 'EBC:inner-entry-event:activation=', visit
          error stop 'EBC:inner-entry-event'
        end if
        checks=checks+1
        if (lbound(inner,1) /= 1) then
          write(*,'(a,i1)') 'EBC:inner-initial-lower:activation=', visit
          error stop 'EBC:inner-initial-lower'
        end if
        checks=checks+1
        if (ubound(inner,1) /= inner_upper) then
          write(*,'(a,i1)') 'EBC:inner-initial-upper:activation=', visit
          error stop 'EBC:inner-initial-upper'
        end if
        checks=checks+1
        if (size(inner) /= inner_extent) then
          write(*,'(a,i1)') 'EBC:inner-initial-size:activation=', visit
          error stop 'EBC:inner-initial-size'
        end if
        checks=checks+1
        if (any(shape(inner) /= [inner_extent])) then
          write(*,'(a,i1)') 'EBC:inner-initial-shape:activation=', visit
          error stop 'EBC:inner-initial-shape'
        end if
        checks=checks+1
        if (any(inner /= inner_value)) then
          write(*,'(a,i1)') 'EBC:inner-initial-values:activation=', visit
          error stop 'EBC:inner-initial-values'
        end if
        checks=checks+1
        if (lbound(outer,1) /= -2) then
          write(*,'(a,i1)') 'EBC:outer-with-inner-lower:activation=', visit
          error stop 'EBC:outer-with-inner-lower'
        end if
        checks=checks+1
        if (ubound(outer,1) /= outer_upper) then
          write(*,'(a,i1)') 'EBC:outer-with-inner-upper:activation=', visit
          error stop 'EBC:outer-with-inner-upper'
        end if
        checks=checks+1
        if (size(outer) /= outer_extent) then
          write(*,'(a,i1)') 'EBC:outer-with-inner-size:activation=', visit
          error stop 'EBC:outer-with-inner-size'
        end if
        checks=checks+1
        if (any(shape(outer) /= [outer_extent])) then
          write(*,'(a,i1)') 'EBC:outer-with-inner-shape:activation=', visit
          error stop 'EBC:outer-with-inner-shape'
        end if
        checks=checks+1
        if (any(outer /= outer_value)) then
          write(*,'(a,i1)') 'EBC:outer-with-inner-values:activation=', visit
          error stop 'EBC:outer-with-inner-values'
        end if
        checks=checks+1
        n=9
        events=events+1
        if (n /= 9) then
          write(*,'(a,i1)') 'EBC:inner-source-redefined:activation=', visit
          error stop 'EBC:inner-source-redefined'
        end if
        checks=checks+1
        if (events /= 6*(visit-1)+4) then
          write(*,'(a,i1)') 'EBC:inner-redefinition-event:activation=', visit
          error stop 'EBC:inner-redefinition-event'
        end if
        checks=checks+1
        if (lbound(inner,1) /= 1) then
          write(*,'(a,i1)') 'EBC:inner-redefined-lower:activation=', visit
          error stop 'EBC:inner-redefined-lower'
        end if
        checks=checks+1
        if (ubound(inner,1) /= inner_upper) then
          write(*,'(a,i1)') 'EBC:inner-redefined-upper:activation=', visit
          error stop 'EBC:inner-redefined-upper'
        end if
        checks=checks+1
        if (size(inner) /= inner_extent) then
          write(*,'(a,i1)') 'EBC:inner-redefined-size:activation=', visit
          error stop 'EBC:inner-redefined-size'
        end if
        checks=checks+1
        if (any(shape(inner) /= [inner_extent])) then
          write(*,'(a,i1)') 'EBC:inner-redefined-shape:activation=', visit
          error stop 'EBC:inner-redefined-shape'
        end if
        checks=checks+1
        if (any(inner /= inner_value)) then
          write(*,'(a,i1)') 'EBC:inner-redefined-values:activation=', visit
          error stop 'EBC:inner-redefined-values'
        end if
        checks=checks+1
        if (lbound(outer,1) /= -2) then
          write(*,'(a,i1)') 'EBC:outer-after-inner-change-lower:activation=', visit
          error stop 'EBC:outer-after-inner-change-lower'
        end if
        checks=checks+1
        if (ubound(outer,1) /= outer_upper) then
          write(*,'(a,i1)') 'EBC:outer-after-inner-change-upper:activation=', visit
          error stop 'EBC:outer-after-inner-change-upper'
        end if
        checks=checks+1
        if (size(outer) /= outer_extent) then
          write(*,'(a,i1)') 'EBC:outer-after-inner-change-size:activation=', visit
          error stop 'EBC:outer-after-inner-change-size'
        end if
        checks=checks+1
        if (any(shape(outer) /= [outer_extent])) then
          write(*,'(a,i1)') 'EBC:outer-after-inner-change-shape:activation=', visit
          error stop 'EBC:outer-after-inner-change-shape'
        end if
        checks=checks+1
        if (any(outer /= outer_value)) then
          write(*,'(a,i1)') 'EBC:outer-after-inner-change-values:activation=', visit
          error stop 'EBC:outer-after-inner-change-values'
        end if
        checks=checks+1
      end block inner_activation
      inner_exits=inner_exits+1
      events=events+1
      if (inner_exits /= visit) then
        write(*,'(a,i1)') 'EBC:inner-exit:activation=', visit
        error stop 'EBC:inner-exit'
      end if
      checks=checks+1
      if (events /= 6*(visit-1)+5) then
        write(*,'(a,i1)') 'EBC:inner-exit-event:activation=', visit
        error stop 'EBC:inner-exit-event'
      end if
      checks=checks+1
      if (lbound(outer,1) /= -2) then
        write(*,'(a,i1)') 'EBC:outer-after-inner-exit-lower:activation=', visit
        error stop 'EBC:outer-after-inner-exit-lower'
      end if
      checks=checks+1
      if (ubound(outer,1) /= outer_upper) then
        write(*,'(a,i1)') 'EBC:outer-after-inner-exit-upper:activation=', visit
        error stop 'EBC:outer-after-inner-exit-upper'
      end if
      checks=checks+1
      if (size(outer) /= outer_extent) then
        write(*,'(a,i1)') 'EBC:outer-after-inner-exit-size:activation=', visit
        error stop 'EBC:outer-after-inner-exit-size'
      end if
      checks=checks+1
      if (any(shape(outer) /= [outer_extent])) then
        write(*,'(a,i1)') 'EBC:outer-after-inner-exit-shape:activation=', visit
        error stop 'EBC:outer-after-inner-exit-shape'
      end if
      checks=checks+1
      if (any(outer /= outer_value)) then
        write(*,'(a,i1)') 'EBC:outer-after-inner-exit-values:activation=', visit
        error stop 'EBC:outer-after-inner-exit-values'
      end if
      checks=checks+1
    end block outer_activation
    outer_exits=outer_exits+1
    events=events+1
    if (outer_exits /= visit) then
      write(*,'(a,i1)') 'EBC:outer-exit:activation=', visit
      error stop 'EBC:outer-exit'
    end if
    checks=checks+1
    if (events /= 6*(visit-1)+6) then
      write(*,'(a,i1)') 'EBC:outer-exit-event:activation=', visit
      error stop 'EBC:outer-exit-event'
    end if
    checks=checks+1
    if (n /= 9) then
      write(*,'(a,i1)') 'EBC:host-source-after-exit:activation=', visit
      error stop 'EBC:host-source-after-exit'
    end if
    checks=checks+1
    if (checks /= 48*visit) then
      write(*,'(a,i1)') 'EBC:block-cycle-checks:activation=', visit
      error stop 'EBC:block-cycle-checks'
    end if
  end do
  if (outer_entries /= 2) error stop 'EBC:block-total-outer_entries'
  if (inner_entries /= 2) error stop 'EBC:block-total-inner_entries'
  if (inner_exits /= 2) error stop 'EBC:block-total-inner_exits'
  if (outer_exits /= 2) error stop 'EBC:block-total-outer_exits'
  if (events /= 12) error stop 'EBC:block-total-events'
  if (checks /= 96) error stop 'EBC:block-total-checks'
  write(*,'(a)') 'EXPLICIT BLOCK BOUNDS OK'
end program explicit_block_bounds
