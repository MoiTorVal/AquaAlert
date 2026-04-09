import Link from "next/link";

export const metadata = {
  title: "Terms of Service | WaterStress",
  description: "WaterStress terms of service",
};

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-[#0a0a0a] pt-32 pb-24 px-8">
      <div className="max-w-3xl mx-auto">
        <Link
          href="/"
          className="text-[#8A8F98] hover:text-white text-sm font-medium"
        >
          &larr; Back to home
        </Link>

        <h1 className="text-4xl font-bold text-[#F7F8F8] mt-8 mb-2">
          Terms of Service
        </h1>
        <p className="text-[#8A8F98] text-sm mb-12">
          Effective date: April 9, 2026
        </p>

        <div className="prose prose-invert prose-sm max-w-none text-white/70 space-y-8">
          <p className="uppercase text-xs leading-relaxed">
            THESE TERMS OF SERVICE (the &quot;Agreement&quot;) GOVERN
            CUSTOMER&apos;S RECEIPT, ACCESS TO, AND USE OF THE SERVICE (AS
            DEFINED BELOW) PROVIDED BY WATERSTRESS, INC.
            (&quot;WaterStress&quot;). IN ACCEPTING THIS AGREEMENT BY (A)
            PURCHASING ACCESS TO THE SERVICE THROUGH AN ONLINE ORDERING PROCESS
            THAT REFERENCES THIS AGREEMENT, (B) SIGNING UP FOR A FREE ACCESS
            PLAN FOR THE SERVICE THROUGH A SCREEN THAT REFERENCES THIS
            AGREEMENT, OR (C) CLICKING A BOX INDICATING ACCEPTANCE, CUSTOMER
            AGREES TO BE BOUND BY ITS TERMS.
          </p>
          <p className="uppercase text-xs leading-relaxed">
            THE INDIVIDUAL ACCEPTING THIS AGREEMENT DOES SO ON BEHALF OF A
            COMPANY OR OTHER LEGAL ENTITY (&quot;Customer&quot;); SUCH
            INDIVIDUAL REPRESENTS AND WARRANTS THAT THEY HAVE THE AUTHORITY TO
            BIND SUCH ENTITY TO THIS AGREEMENT. IF THE INDIVIDUAL ACCEPTING THIS
            AGREEMENT DOES NOT HAVE SUCH AUTHORITY, OR THE APPLICABLE ENTITY
            DOES NOT AGREE WITH THESE TERMS AND CONDITIONS, SUCH INDIVIDUAL MUST
            NOT ACCEPT THIS AGREEMENT AND MAY NOT USE OR RECEIVE THE SERVICE.
            CAPITALIZED TERMS HAVE THE DEFINITIONS SET FORTH HEREIN. THE PARTIES
            AGREE AS FOLLOWS:
          </p>
          {/* Table of Contents */}
          <div className="border border-white/10 rounded-lg p-6 space-y-2">
            <h2 className="text-base font-semibold text-[#F7F8F8] mb-3">
              Table of Contents
            </h2>
            <ol className="list-decimal list-inside space-y-1 text-sm">
              <li>The Service</li>
              <li>Restrictions</li>
              <li>Third-Party Applications</li>
              <li>Payment Obligations</li>
              <li>Term and Termination</li>
              <li>Warranties and Disclaimers</li>
              <li>Limitation of Liability</li>
              <li>Confidentiality</li>
              <li>Data</li>
              <li>General Terms</li>
            </ol>
          </div>
          {/* 1. The Service */}
          <h2 className="text-xl font-semibold text-[#F7F8F8] pt-4">
            1. The Service
          </h2>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            1.1 Service Description
          </h3>
          <p>
            WaterStress is the owner and provider of a cloud-based water stress
            monitoring and irrigation decision support platform (the
            &quot;Service&quot;). The Service ingests publicly available weather
            and evapotranspiration data, field configurations, crop parameters,
            and optional sensor telemetry to compute soil water balance models,
            generate irrigation scheduling recommendations, and produce water
            stress forecasts. Anything Customer (including Users) posts,
            uploads, shares, stores, or otherwise provides through the Service
            is considered a &quot;User Submission.&quot; Customer is solely
            responsible for all User Submissions it contributes to the Service.
            Further terms regarding User Submissions, including ownership, are
            in Section 9.2 below. The Service may also include templates, help
            documents, agronomic reference materials, and other documents or
            information that can assist Customer in using the Service
            (&quot;WaterStress Content&quot;). Customer will not receive or have
            access to the code or software that underlies the Service
            (collectively the &quot;Software&quot;) or receive a copy of the
            Software itself.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            1.2 Customer&apos;s Subscription
          </h3>
          <p>
            Subject to the terms of this Agreement, Customer may purchase a
            subscription to, and has the right to access and use, the Service as
            specified in one or more ordering screens agreed to by the parties
            through WaterStress&apos;s website that reference this Agreement and
            describe the business terms related to Customer&apos;s subscription
            (&quot;Order(s)&quot;). All subscriptions will be for the period
            described on the applicable Order (&quot;Subscription Period&quot;).
            Use of and access to the Service is permitted only by individuals
            authorized by Customer and for Customer&apos;s own internal business
            purposes and not for the benefit of any third party
            (&quot;Users&quot;).
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            1.3 WaterStress&apos;s Ownership
          </h3>
          <p>
            WaterStress owns the Service, Software, WaterStress Content,
            Documentation, and anything else provided by WaterStress to Customer
            (collectively the &quot;WaterStress Materials&quot;). WaterStress
            retains all right, title, and interest (including, without
            limitation, all patent, copyright, trademark, trade secret, and
            other intellectual property rights) in and to the WaterStress
            Materials, all related and underlying technology and any updates,
            enhancements, upgrades, modifications, patches, workarounds, and
            fixes thereto and all derivative works of or modifications to any of
            the foregoing. There are no implied licenses under this Agreement
            and any rights not expressly granted to Customer in this Agreement
            are expressly reserved by WaterStress.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            1.4 Agronomic Disclaimer
          </h3>
          <p>
            The Service provides irrigation scheduling recommendations and water
            stress forecasts based on mathematical models (including the FAO-56
            soil water balance methodology), publicly available weather data,
            and information provided by Customer. These outputs are
            decision-support tools and do not constitute professional agronomic
            advice. Customer acknowledges that actual field conditions may
            differ from modeled conditions and that WaterStress does not
            guarantee crop outcomes, yields, or water savings. Customer is
            solely responsible for all irrigation decisions made using the
            Service.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            1.5 Permissions
          </h3>
          <p>
            {" "}
            13:42 [420/1980] The Service contains customizable settings allowing
            each User to give permission to other Users to perform various tasks
            within the Service (&quot;Permissions&quot;). It is solely
            Customer&apos;s responsibility to set and manage all Permissions,
            including which Users can set such Permissions. Accordingly,
            WaterStress will have no responsibility for managing Permissions and
            no liability for the Permissions set by Customer and its Users.
            Customer may, at its option, provide access to the Service and
            Documentation to its Affiliates, in which case all rights granted,
            and obligations incurred, under this Agreement will also inure to
            the benefit of such Affiliates. Customer represents and warrants
            that it is fully responsible for any breach of this Agreement by its
            Affiliates and that Customer has the power to negotiate this
            Agreement on behalf of its Affiliates. Customer will also be
            responsible for all payment obligations under this Agreement
            regardless of whether the use of the Service is by Customer or its
            Affiliates. Any claim by an Affiliate against WaterStress will be
            brought by Customer and not the Affiliate. For the purposes of this
            Agreement &quot;Affiliate&quot; will mean an entity directly or
            indirectly controlling, controlled by, or under common control with
            that party (where &quot;control&quot; means the ownership or
            control, directly or indirectly, of more than fifty percent (50%) of
            all the voting power of the shares (or other securities or rights)
            entitled to vote for the election of directors or other governing
            authority).
          </p>
          {/* 2. Restrictions */}
          <h2 className="text-xl font-semibold text-[#F7F8F8] pt-4">
            2. Restrictions
          </h2>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            2.1 Customer&apos;s Responsibilities
          </h3>
          <p>
            Customer is responsible for all activity on its Users&apos; accounts
            unless such activity is caused by a third-party bad actor able to
            access Customer&apos;s account by exploiting vulnerabilities in the
            Service itself. Customer will ensure that its Users are aware of and
            bound by obligations and/or restrictions stated in this Agreement
            and Customer will be responsible for breach of any such obligation
            and/or restriction by a User.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            2.2 Use Restrictions
          </h3>
          <p>
            Customer agrees that it will not, and will not allow Users or third
            parties to, directly or indirectly:
          </p>
          <ul className="list-disc list-inside space-y-1">
            <li>
              modify, translate, copy, or create derivative works based on the
              Service;
            </li>
            <li>
              reverse assemble, reverse compile, reverse engineer, decompile, or
              otherwise attempt to discover the object code, source code,
              non-public APIs, or underlying ideas or algorithms of the Service,
              except as and only to the extent this restriction is prohibited by
              law;
            </li>
            <li>
              license, sublicense, sell, resell, rent, lease, transfer, assign,
              distribute, time share, or otherwise commercially exploit or make
              the Service available to any third party;
            </li>
            <li>
              remove or obscure any copyright, trademark, or other proprietary
              notices, legends, or WaterStress branding contained in or on the
              Service;
            </li>
            <li>
              use the Service in any way that violates any applicable federal,
              state, local, or international law or regulation;
            </li>
            <li>
              attempt to gain unauthorized access to, interfere with, damage, or
              disrupt any parts of the Service, including by introducing viruses
              and other harmful code or by using denial-of-service attacks or
              similar methods;
            </li>
            <li>
              use or access the Service to build or support products or services
              competitive to the Service;
            </li>
            <li>
              attempt to probe, scan, or test the vulnerability of the Service
              or any WaterStress system or network;
            </li>
            <li>
              use or access the Service in violation of U.S. or applicable
              non-U.S. laws relating to economic or trade sanctions;
            </li>
            <li>
              use model outputs, water balance calculations, or stress forecasts
              generated by the Service to make representations to any regulatory
              body or court as though they were certified agronomic assessments,
              without independent verification by a qualified professional.
            </li>
          </ul>
          <p>
            If Customer (including Users) is using the Service in a manner that,
            in WaterStress&apos;s reasonable judgment, causes or is likely to
            cause significant harm to WaterStress or the Service, then
            WaterStress may suspend Customer&apos;s access to the Service.
            WaterStress will use commercially reasonable efforts to (x) provide
            Customer with notice and an opportunity to remedy such violation or
            threat prior to any such suspension; (y) limit the suspension to
            only accounts involved in the activities in question; and (z) remove
            the suspension as quickly as practicable after the circumstances
            leading to the suspension have been resolved.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            2.3 API Access Restrictions
          </h3>
          <p>
            As part of its Service, WaterStress may provide Customer with access
            to one or more application program interfaces (&quot;API(s)&quot;).
            WaterStress may, in its sole discretion, set and enforce limits on
            Customer&apos;s use of the API, and Customer agrees to adhere to
            such limits. WaterStress may also suspend Customer&apos;s access to
            the API or cease providing the API at any time.
          </p>
          {/* 3. Third-Party Applications */}
          <h2 className="text-xl font-semibold text-[#F7F8F8] pt-4">
            3. Third-Party Applications
          </h2>
          <p>
            The Service may work together with third-party products, services,
            or applications that are not owned or controlled by WaterStress
            (e.g., CIMIS, weather data providers, sensor hardware platforms,
            farm management software) (&quot;Third-Party Applications&quot;),
            and Customer, at its sole option, may choose to use such Third-Party
            Applications. If necessary for the Service and the Third-Party
            Application to work together, Customer will provide its login
            information to WaterStress for the sole purpose of WaterStress
            providing the Service to Customer, and Customer represents and
            warrants that Customer has the right to provide such login
            information without breach of any terms that govern Customer&apos;s
            use of the applicable Third-Party Application. WaterStress does not
            endorse such Third-Party Applications. Customer acknowledges and
            agrees that this Agreement does not apply to Customer&apos;s use of
            such Third-Party Applications. WaterStress expressly disclaims all
            representations and warranties relating to any Third-Party
            Applications. WaterStress will have no liability or other obligation
            of any kind arising out of or related to any Third-Party
            Applications, including arising from Customer&apos;s use or
            inability to use Third-Party Applications.
          </p>
          {/* 4. Payment Obligations */}
          <h2 className="text-xl font-semibold text-[#F7F8F8] pt-4">
            4. Payment Obligations
          </h2>
          <h3 className="text-lg font-medium text-[#F7F8F8]">4.1 Fees</h3>
          <p>
            Customer will pay for access to and use of the Service as set forth
            on the applicable Order (&quot;Fees&quot;). All Fees will be paid in
            the currency stated in the applicable Order or, if no currency is
            specified, U.S. dollars. Payment obligations are non-cancelable and,
            except as expressly stated in this Agreement, non-refundable.
            WaterStress may modify its Fees or introduce new fees in its sole
            discretion. Customer always has the right to choose not to renew its
            subscription if it does not agree with any new or revised Fees.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">4.2 Payment</h3>
          <p>
            WaterStress, either directly or through its third-party payment
            processor (&quot;Payment Processor&quot;), will charge Customer for
            the Fees via credit card or ACH payment, pursuant to the payment
            information provided by Customer. WaterStress will have the right to
            charge Customer&apos;s payment method for any services provided
            under the Order, including recurring Fees. It is Customer&apos;s
            sole responsibility to provide WaterStress with current and
            up-to-date payment information; failure to provide such information
            may result in suspension of Customer&apos;s access to the Service.
            If Customer pays the Fees through a Payment Processor, such payment
            processing will be subject to the terms, conditions, and privacy
            policies of the Payment Processor in addition to this Agreement.
            WaterStress is not responsible for any error by, or other acts or
            omissions of, the Payment Processor. WaterStress reserves the right
            to correct any errors or mistakes that the Payment Processor makes
            even if WaterStress has already requested or received payment.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">4.3 Taxes</h3>
          <p>
            Fees do not include any taxes, levies, duties, or similar
            governmental assessments of any nature, including, for example,
            value-added, sales, use, or withholding taxes, assessable by any
            jurisdiction whatsoever (collectively, &quot;Taxes&quot;). Customer
            is responsible for paying all Taxes associated with its purchases
            hereunder. If WaterStress has the legal obligation to pay or collect
            Taxes for which Customer is responsible under this section,
            WaterStress will invoice Customer and Customer will pay that amount
            unless Customer provides WaterStress with a valid tax exemption
            certificate authorized by the appropriate taxing authority in
            advance. For clarity, WaterStress is solely responsible for taxes
            assessable against it based on its income, property, and employees.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            4.4 Failure to Pay
          </h3>
          <p>
            If Customer fails to pay any Fees when due, WaterStress may suspend
            Customer&apos;s access to the Service pending payment of such
            overdue amounts. Customer also authorizes WaterStress to make
            multiple re-attempts at charging Customer&apos;s payment instrument
            if an initial charge attempt is unsuccessful. If Customer believes
            that WaterStress has billed Customer incorrectly, Customer must
            contact WaterStress no later than sixty (60) days after the closing
            date on the first billing statement in which the error or problem
            appeared, to receive an adjustment or credit.
          </p>
          {/* 5. Term and Termination */}
          <h2 className="text-xl font-semibold text-[#F7F8F8] pt-4">
            5. Term and Termination
          </h2>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            5.1 Agreement Term and Renewals
          </h3>
          <p>
            Subscriptions to access and use the Service commence on the start
            date stated on the applicable Order (&quot;Subscription Start
            Date&quot;) and continue for the duration of the Subscription
            Period. Customer may choose not to renew its Subscription Period by
            notifying WaterStress at billing@waterstress.io (provided that
            WaterStress confirms such cancellation in writing) or by modifying
            its subscription through Customer&apos;s account within the Service.
            This Agreement will become effective on the first day of the
            Subscription Period and remain effective for the duration of the
            Subscription Period stated on the Order along with any renewals of
            the Subscription Period (&quot;Term&quot;). If Customer cancels or
            does not renew its paid subscription, Customer&apos;s subscription
            will automatically be downgraded to a version of the Service with
            diminished features and functionality that WaterStress offers to
            unpaid subscribers (&quot;Free Version&quot;). If Customer or
            WaterStress terminates this Agreement or Customer deletes its
            workspace within the Service, Customer will not have access to the
            Free Version.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            5.2 Termination
          </h3>
          <p>
            Either party may terminate this Agreement upon written notice to the
            other party if the other party materially breaches this Agreement
            and such breach is not cured within thirty (30) days after the
            breaching party&apos;s receipt of such notice. WaterStress may
            terminate Customer&apos;s access to the Free Version at any time
            upon notice to Customer.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            5.3 Effect of Termination
          </h3>
          <p>
            If Customer terminates this Agreement because of WaterStress&apos;s
            uncured breach, WaterStress will refund any unused, prepaid Fees for
            the remainder of the then-current Subscription Period. If
            WaterStress terminates this Agreement because of Customer&apos;s
            uncured breach, Customer will pay any unpaid Fees covering the
            remainder of the then-current Subscription Period after the
            effective date of termination. In no event will any termination
            relieve Customer of the obligation to pay any Fees payable to
            WaterStress for the period prior to the effective date of
            termination. Upon any termination of this Agreement, all rights and
            licenses granted by WaterStress hereunder will immediately
            terminate; Customer will no longer have the right to access or use
            the Service. Within thirty (30) days of termination, upon
            Customer&apos;s request, WaterStress will delete Customer&apos;s
            User Information, including passwords and all related information,
            files, User Submissions, and field data, unless Customer requests an
            earlier deletion in writing. WaterStress may delete all User
            Submissions or User Information if Customer maintains an account in
            the Free Version but such account is not used for a period of one
            (1) year or more.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">5.4 Survival</h3>
          <p>
            Sections titled &quot;WaterStress&apos;s Ownership,&quot;
            &quot;Agronomic Disclaimer,&quot; &quot;Third-Party
            Applications,&quot; &quot;Payment Obligations,&quot; &quot;Term and
            Termination,&quot; &quot;Warranty Disclaimer,&quot; &quot;Limitation
            of Liability,&quot; &quot;Confidentiality,&quot; &quot;Data,&quot;
            and &quot;General Terms&quot; will survive any termination or
            expiration of this Agreement.
          </p>
          {/* 6. Warranties and Disclaimers */}
          <h2 className="text-xl font-semibold text-[#F7F8F8] pt-4">
            6. Warranties and Disclaimers
          </h2>
          <h3 className="text-lg font-medium text-[#F7F8F8]">6.1 Warranties</h3>
          <p>
            Customer represents and warrants that all User Submissions submitted
            by Users follow all applicable laws, rules, and regulations, and
            that any field data, crop parameters, or sensor readings provided to
            the Service are accurate to the best of Customer&apos;s knowledge.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            6.2 Warranty Disclaimer
          </h3>
          <p className="uppercase text-xs leading-relaxed">
            EXCEPT AS EXPRESSLY PROVIDED FOR HEREIN, THE SERVICE AND ALL RELATED
            COMPONENTS AND INFORMATION ARE PROVIDED ON AN &quot;AS IS&quot; AND
            &quot;AS AVAILABLE&quot; BASIS WITHOUT ANY WARRANTIES OF ANY KIND,
            AND WATERSTRESS EXPRESSLY DISCLAIMS ANY AND ALL WARRANTIES, WHETHER
            EXPRESS OR IMPLIED, INCLUDING THE IMPLIED WARRANTIES OF
            MERCHANTABILITY, TITLE, FITNESS FOR A PARTICULAR PURPOSE, AND
            NON-INFRINGEMENT. CUSTOMER ACKNOWLEDGES THAT WATERSTRESS DOES NOT
            WARRANT THAT THE SERVICE WILL BE UNINTERRUPTED, TIMELY, SECURE, OR
            ERROR-FREE. WATERSTRESS DOES NOT WARRANT THE ACCURACY OF ANY WATER
            BALANCE CALCULATIONS, STRESS FORECASTS, IRRIGATION RECOMMENDATIONS,
            OR OTHER MODEL OUTPUTS. CUSTOMER ACKNOWLEDGES THAT SUCH OUTPUTS ARE
            ESTIMATES BASED ON MATHEMATICAL MODELS AND PUBLICLY AVAILABLE DATA
            THAT MAY CONTAIN ERRORS OR INACCURACIES. SOME JURISDICTIONS DO NOT
            ALLOW THE DISCLAIMER OF CERTAIN TYPES OF WARRANTIES. THE FOREGOING
            DISCLAIMERS WILL NOT APPLY TO THE EXTENT PROHIBITED BY APPLICABLE
            LAW.
          </p>
          {/* 7. Limitation of Liability */}
          <h2 className="text-xl font-semibold text-[#F7F8F8] pt-4">
            7. Limitation of Liability
          </h2>
          <p className="uppercase text-xs leading-relaxed">
            NOTWITHSTANDING ANYTHING TO THE CONTRARY IN THIS AGREEMENT,
            WATERSTRESS WILL NOT BE LIABLE WITH RESPECT TO ANY CAUSE RELATED TO
            OR ARISING OUT OF THIS AGREEMENT, WHETHER IN AN ACTION BASED ON A
            CONTRACT, TORT (INCLUDING NEGLIGENCE AND STRICT LIABILITY) OR ANY
            OTHER LEGAL THEORY, HOWEVER ARISING, FOR (A) INDIRECT, SPECIAL,
            INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING BUT NOT LIMITED TO
            CROP LOSS, REDUCED YIELDS, WATER WASTE, REGULATORY PENALTIES, OR
            LOSS OF REVENUE ARISING FROM RELIANCE ON THE SERVICE&apos;S OUTPUTS,
            (B) ANY DAMAGES BASED ON USE OR ACCESS, INTERRUPTION, DELAY, OR
            INABILITY TO USE THE SERVICE, LOST REVENUES OR PROFITS, DELAYS,
            INTERRUPTION OR LOSS OF SERVICES, BUSINESS OR GOODWILL, LOSS OR
            CORRUPTION OF DATA, LOSS RESULTING FROM SYSTEM OR SYSTEM SERVICE
            FAILURE, MALFUNCTION OR SHUTDOWN, FAILURE TO ACCURATELY TRANSFER,
            READ, OR TRANSMIT INFORMATION, FAILURE TO UPDATE OR PROVIDE CORRECT
            INFORMATION, SYSTEM INCOMPATIBILITY OR PROVISION OF INCORRECT
            COMPATIBILITY INFORMATION, OR BREACHES IN SYSTEM SECURITY, OR (C)
            ANY DAMAGES THAT IN THE AGGREGATE EXCEED THE TOTAL FEES PAID OR
            PAYABLE BY CUSTOMER FOR THE SERVICE DURING THE TWELVE (12) MONTH
            PERIOD IMMEDIATELY PRECEDING THE EVENT WHICH GIVES RISE TO SUCH
            DAMAGES. THESE LIMITATIONS WILL APPLY WHETHER OR NOT A PARTY HAS
            BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES AND NOTWITHSTANDING
            ANY FAILURE OF ESSENTIAL PURPOSE OF ANY LIMITED REMEDY.
          </p>
          {/* 8. Confidentiality */}
          <h2 className="text-xl font-semibold text-[#F7F8F8] pt-4">
            8. Confidentiality
          </h2>
          <h3 className="text-lg font-medium text-[#F7F8F8]">8.1 Definition</h3>
          <p>
            Each party (the &quot;Receiving Party&quot;) understands that the
            other party (the &quot;Disclosing Party&quot;) may disclose
            business, technical, or financial information relating to the
            Disclosing Party&apos;s business that reasonably should be
            understood to be confidential given the nature of the information
            and the circumstances of disclosure (hereinafter referred to as the
            &quot;Confidential Information&quot; of the Disclosing Party).
            WaterStress&apos;s Confidential Information includes non-public
            information regarding features, functionality, and performance of
            the Service, including proprietary model parameters and algorithms.
            Customer&apos;s Confidential Information includes the User
            Information, User Submissions, and field-level agricultural data.
            This Agreement and the information in all Orders will be deemed the
            Confidential Information of both parties. Notwithstanding the above,
            Confidential Information does not include information that (a) is or
            becomes generally available to the public without breach of any
            obligation owed to the Disclosing Party; (b) was known to the
            Receiving Party prior to its disclosure by the Disclosing Party; (c)
            is received from a third party without breach of any obligation owed
            to the Disclosing Party; or (d) was independently developed by the
            Receiving Party without use or reference to the Disclosing
            Party&apos;s Confidential Information.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            8.2 Protection and Use of Confidential Information
          </h3>
          <p>
            The Receiving Party will (a) protect the Disclosing Party&apos;s
            Confidential Information using the same degree of care used to
            protect its own confidential or proprietary information of like
            importance, but in any case using no less than a reasonable degree
            of care, (b) limit access to the Confidential Information to those
            employees, affiliates, subcontractors, agents, consultants, legal
            advisors, financial advisors, and contractors
            (&quot;Representatives&quot;) who need to know such information in
            connection with this Agreement and who are bound by confidentiality
            and non-use obligations just as protective as the terms of this
            Agreement; (c) except as expressly set forth herein, make all
            commercially reasonable efforts not to disclose any of Disclosing
            Party&apos;s Confidential Information to any third parties without
            the Disclosing Party&apos;s prior written consent; and (d) will not
            use the Disclosing Party&apos;s Confidential Information for any
            purpose other than to fulfill its obligations under this Agreement.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            8.3 Compelled Access or Disclosure
          </h3>
          <p>
            The Receiving Party may access or disclose Confidential Information
            of the Disclosing Party if it is required by law; provided, however,
            that the Receiving Party gives the Disclosing Party prior notice of
            the compelled access or disclosure (to the extent legally permitted)
            and reasonable assistance, at the Disclosing Party&apos;s cost, if
            the Disclosing Party wishes to contest the access or disclosure.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">8.4 Feedback</h3>
          <p>
            Customer may from time to time provide suggestions, comments, or
            other feedback with respect to the Service (&quot;Feedback&quot;).
            Feedback will only refer to suggestions, comments, or other feedback
            provided to WaterStress specifically regarding the Service and will
            not include User Information or User Submissions. Customer hereby
            grants to WaterStress a royalty-free, worldwide, perpetual,
            irrevocable, fully transferable and sublicensable right and license
            to use, disclose, reproduce, modify, create derivative works from,
            distribute, display, and otherwise exploit any Feedback as
            WaterStress sees fit, entirely without obligation or restriction of
            any kind, except that WaterStress will not identify Customer as the
            provider of such Feedback.
          </p>{" "}
          {/* 9. Data */}
          <h2 className="text-xl font-semibold text-[#F7F8F8] pt-4">9. Data</h2>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            9.1 User Information
          </h3>
          <p>
            Customer and its Users are required to provide information such as
            name, email address, username, IP address, browser, and operating
            system (&quot;User Information&quot;) upon logging into the Service.
            Customer grants WaterStress and its subcontractors the right to
            store, process, and retrieve the User Information in connection with
            Customer&apos;s use of the Service. Customer represents and warrants
            that it has obtained all necessary rights to transfer User
            Information to WaterStress and to process the User Information as
            contemplated by this Agreement. Customer is responsible for all User
            Information. Customer (on behalf of its Users) grants WaterStress
            the right to access, use, process, copy, distribute (to Users),
            perform (for Users), export (to Users), and display (for Users) User
            Information, only as reasonably necessary (a) to provide the Service
            to Customer; (b) to prevent or address service, security, support,
            or technical issues; (c) as required by law; and (d) as expressly
            permitted in writing by Customer.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            9.2 User Submissions
          </h3>
          <p>
            Customer grants WaterStress and its subcontractors a non-exclusive,
            worldwide, royalty-free, paid-up, transferable right and license to
            use, process, and display (to Users) User Submissions for the sole
            purpose of providing the Service to Customer. Except for the limited
            rights and licenses granted in this Agreement, Customer will own all
            right, title, and interest in and to the User Submissions, including
            all field data, crop configurations, and sensor readings, and there
            are no implied licenses under this Agreement.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            9.3 Service Data
          </h3>
          <p>
            As Customer (including its Users) interacts with the Service, the
            Service collects data pertaining to the performance of the Service
            and measures of the operation of the Service (&quot;Service
            Data&quot;). Notwithstanding anything else to the contrary herein,
            provided that the Service Data is aggregated and anonymized, and no
            User Information, User Submissions, or any other personal
            identifying information of Customer is revealed to any third party,
            the parties agree that WaterStress is free to use the Service Data
            in any manner, including to improve model accuracy across the
            platform. WaterStress owns all right, title, and interest in and to
            such Service Data. For clarity, this section does not give
            WaterStress the right to identify Customer (including its Users) as
            the source of any Service Data.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            9.4 SGMA Compliance Reporting
          </h3>
          <p>
            If Customer opts in to SGMA compliance reporting features, Customer
            authorizes WaterStress to compile and transmit field-level water use
            summaries to the applicable Groundwater Sustainability Agency
            (&quot;GSA&quot;) on Customer&apos;s behalf. WaterStress will share
            only the data categories and in the format that Customer has
            approved prior to any such transmission. Customer may revoke this
            authorization at any time through the Service settings.
          </p>{" "}
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            9.5 Data Protection
          </h3>
          <p>
            WaterStress has established and implemented reasonable information
            security practices regarding the protection of User Submissions and
            User Information (collectively &quot;Customer Data&quot;), including
            administrative, technical, and physical security processes.
            Notwithstanding the foregoing, Customer is responsible for
            maintaining appropriate security, protection, and backup of its
            hardware, software, systems, information, and Customer Data.
            WaterStress will, during the Term, process all Customer Data in
            accordance with WaterStress&apos;s data protection agreement, a copy
            of which can be found at waterstress.io/dpa.
          </p>
          {/* 10. General Terms */}
          <h2 className="text-xl font-semibold text-[#F7F8F8] pt-4">
            10. General Terms
          </h2>
          <h3 className="text-lg font-medium text-[#F7F8F8]">10.1 Publicity</h3>
          <p>
            Provided that Customer gives its prior written consent, WaterStress
            may identify Customer and use and display Customer&apos;s name,
            logo, trademarks, or service marks on WaterStress&apos;s website and
            in WaterStress&apos;s marketing materials.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            10.2 Force Majeure
          </h3>
          <p>
            WaterStress will not be liable by reason of any failure or delay in
            the performance of its obligations on account of events beyond the
            reasonable control of WaterStress, which may include failure by a
            third-party hosting provider or utility provider, strikes,
            shortages, riots, fires, acts of God, war, terrorism, governmental
            action, drought, flood, extreme weather events, or disruptions to
            public weather data sources.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">10.3 Changes</h3>
          <p>
            Customer acknowledges that the Service is an online,
            subscription-based product, and that to provide improved customer
            experience WaterStress may make changes to the Service, provided
            however WaterStress will not materially decrease the core
            functionality of the Service. WaterStress may also unilaterally
            modify the terms of this Agreement by notifying Customer at least
            thirty (30) days prior to such changes taking effect and posting
            such changes at waterstress.io/terms.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            10.4 Relationship of the Parties
          </h3>
          <p>
            The parties are independent contractors. This Agreement does not
            create a partnership, franchise, joint venture, agency, fiduciary,
            or employment relationship between the parties.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            10.5 No Third-Party Beneficiaries
          </h3>
          <p>
            There are no third-party beneficiaries to this Agreement; a person
            who is not a party to this Agreement may not enforce any of its
            terms under any applicable law.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            10.6 Email Communications
          </h3>
          <p>
            Notices under this Agreement will be provided as follows: (a) all
            notices regarding the Service will be sent by email, although
            WaterStress may instead choose to provide notice to Customer through
            the Service, (b) notices to WaterStress must be sent to
            legal@waterstress.io, and (c) all notices to Customer will be sent
            to the email(s) provided through the Service. Notices will be deemed
            to have been duly given the business day after they are sent.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            10.7 Amendment and Waivers
          </h3>
          <p>
            No modification or amendment to this Agreement will be effective
            unless made in writing and signed or accepted by an authorized
            representative of both parties. No failure or delay by either party
            in exercising any right under this Agreement will constitute a
            waiver of that right.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            10.8 Severability
          </h3>
          <p>
            This Agreement will be enforced to the fullest extent permitted
            under applicable law. If any provision of this Agreement is held by
            a court of competent jurisdiction to be contrary to law, the
            provision will be modified by the court and interpreted so as best
            to accomplish the objectives of the original provision to the
            fullest extent permitted by law, and the remaining provisions of
            this Agreement will remain in effect.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            10.9 Assignment
          </h3>
          <p>
            Neither party will assign or delegate any of its rights or
            obligations hereunder, whether by operation of law or otherwise,
            without the prior written consent of the other party (not to be
            unreasonably withheld). Notwithstanding the foregoing, WaterStress
            may assign this Agreement in its entirety (including all Orders),
            without the consent of Customer, in connection with a merger,
            acquisition, corporate reorganization, or sale of all or
            substantially all WaterStress&apos;s assets. Any purported
            assignment in violation of this section is void.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            10.10 Governing Law and Venue
          </h3>
          <p>
            This Agreement, and any disputes arising out of or related hereto,
            will be governed exclusively by the internal laws of the State of
            California, without regard to its conflicts of laws rules or the
            United Nations Convention on the International Sale of Goods. The
            state and federal courts located in Tulare County, California will
            have exclusive jurisdiction to adjudicate any dispute arising out of
            or relating to this Agreement. Each party hereby consents and
            submits to the exclusive jurisdiction of such courts. Each party
            also hereby waives any right to jury trial in connection with any
            action or litigation in any way arising out of or related to this
            Agreement. In any action or proceeding to enforce rights under this
            Agreement, the prevailing party will be entitled to recover its
            reasonable costs and attorney&apos;s fees.
          </p>
          <h3 className="text-lg font-medium text-[#F7F8F8]">
            10.11 Entire Agreement
          </h3>
          <p>
            This Agreement, including all referenced pages and Orders, if
            applicable, constitutes the entire agreement between the parties and
            supersedes all prior and contemporaneous agreements, proposals, or
            representations, written or oral, concerning its subject matter.
          </p>
        </div>
      </div>
    </main>
  );
}
